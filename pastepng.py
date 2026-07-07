"""
PastePNG - save the clipboard image into the focused Explorer folder as a PNG.

Runs quietly in the system tray. Copy an image (for example with Win+Shift+S),
click the Explorer window you want, press Ctrl+V, and the image is written into
that folder as a PNG file.

Open source, MIT licensed.
Requirements: pip install pillow pywin32 keyboard pystray
"""

import os
import sys
import ctypes
import datetime
import traceback

from PIL import Image, ImageGrab
import win32gui
import win32com.client
import pythoncom
import keyboard
import pystray


APP_NAME = "PastePNG"
APP_ID = "PastePNG.App"          # AppUserModelID, helps Windows show toasts
HOTKEY = "ctrl+v"
BASE_NAME = "Screenshot"
EXT = ".png"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

LOG_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
LOG_PATH = os.path.join(LOG_DIR, "pastepng.log")

MB_OK = 0x0
MB_ICONERROR = 0x10
MB_ICONINFO = 0x40

# Toggled from the tray menu.
STATE = {"enabled": True}
# Keep the single-instance mutex handle alive for the process lifetime.
_MUTEX = None


# ------------------------------------------------------------ Dialogs / log
def message_box(text, title=APP_NAME, flags=MB_OK):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, flags)
    except Exception:
        pass


def log_line(text):
    """Append one line to the log so you can see what each Ctrl+V did."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {text}\n")
    except Exception:
        pass


def already_running():
    """True if another PastePNG instance already holds the named mutex."""
    global _MUTEX
    ERROR_ALREADY_EXISTS = 183
    try:
        _MUTEX = ctypes.windll.kernel32.CreateMutexW(
            None, False, "PastePNG_singleton_mutex")
        return ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS
    except Exception:
        return False


# ------------------------------------------------------------ Explorer
def _exe_of(window):
    try:
        return os.path.basename(window.FullName).lower()
    except Exception:
        return ""


def focused_explorer_path():
    """Return the folder path of the focused Explorer window, or None."""
    fg = win32gui.GetForegroundWindow()
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        windows = shell.Windows()
    except Exception:
        return None
    for w in windows:
        try:
            if _exe_of(w) != "explorer.exe":
                continue
            if int(w.HWND) == int(fg):
                path = w.Document.Folder.Self.Path
                if path and os.path.isdir(path):
                    return path
                return None
        except Exception:
            continue
    return None


def unique_path(folder):
    """Screenshot.png, then Screenshot (1).png, and so on."""
    cand = os.path.join(folder, BASE_NAME + EXT)
    if not os.path.exists(cand):
        return cand
    i = 1
    while True:
        cand = os.path.join(folder, f"{BASE_NAME} ({i}){EXT}")
        if not os.path.exists(cand):
            return cand
        i += 1


def clipboard_image():
    data = ImageGrab.grabclipboard()
    return data if isinstance(data, Image.Image) else None


# ------------------------------------------------------------ Feedback
def notify(icon, message):
    """Always update the tooltip, and try a toast on top of that."""
    try:
        icon.title = f"{APP_NAME}: {message}"
    except Exception:
        pass
    try:
        icon.notify(message, APP_NAME)   # may be suppressed by Windows settings
    except Exception:
        pass


# ------------------------------------------------------------ Hotkey
def on_paste(icon):
    """Runs on Ctrl+V. Stays out of the way unless both conditions hold."""
    if not STATE["enabled"]:
        return
    # The keyboard callback runs on its own thread, so COM has to be
    # initialized here or Shell access fails silently.
    pythoncom.CoInitialize()
    try:
        folder = focused_explorer_path()
        if not folder:
            log_line("Ctrl+V: no Explorer window focused, skipped")
            return
        img = clipboard_image()
        if img is None:
            log_line(f"Ctrl+V: '{folder}' focused but clipboard has no image")
            return
        path = unique_path(folder)
        img.save(path, "PNG")
        log_line(f"Saved {path}")
        notify(icon, f"Saved {os.path.basename(path)}")
    except Exception as e:
        log_line(f"Error: {e}")
    finally:
        pythoncom.CoUninitialize()


# ------------------------------------------------------------ Autostart
def _run_target():
    # The --startup flag keeps the login launch silent (no confirmation box).
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pyw}" "{os.path.abspath(__file__)}" --startup'


def autostart_enabled():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
        return True
    except OSError:
        return False


def set_autostart(enable):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if enable:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _run_target())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except FileNotFoundError:
                pass


# ------------------------------------------------------------ Tray
def load_icon_image():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("assets/icon.png", "icon.png"):
        p = os.path.join(here, name)
        if os.path.exists(p):
            return Image.open(p)
    return Image.new("RGBA", (64, 64), (79, 70, 229, 255))


def open_log(_icon, _item):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        if not os.path.exists(LOG_PATH):
            open(LOG_PATH, "a").close()
        os.startfile(LOG_PATH)
    except Exception:
        pass


def build_tray():
    icon = pystray.Icon(APP_NAME)
    icon.icon = load_icon_image()
    icon.title = f"{APP_NAME}: Ctrl+V saves the clipboard image to the current folder"

    def toggle_enabled(_icon, _item):
        STATE["enabled"] = not STATE["enabled"]

    def toggle_autostart(_icon, _item):
        set_autostart(not autostart_enabled())

    def quit_app(_icon, _item):
        _icon.stop()

    icon.menu = pystray.Menu(
        pystray.MenuItem("Enabled", toggle_enabled,
                         checked=lambda item: STATE["enabled"]),
        pystray.MenuItem("Start with Windows", toggle_autostart,
                         checked=lambda item: autostart_enabled()),
        pystray.MenuItem("Open log", open_log),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    return icon


def main():
    silent = "--startup" in sys.argv
    try:
        # Give the process an identity so Windows is willing to show toasts.
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

        if already_running():
            if not silent:
                message_box(f"{APP_NAME} is already running in the system tray.",
                            APP_NAME, MB_ICONINFO)
            return

        log_line(f"{APP_NAME} started")
        icon = build_tray()
        keyboard.add_hotkey(HOTKEY, lambda: on_paste(icon), suppress=False)

        if not silent:
            message_box(
                f"{APP_NAME} is running.\n\n"
                "1) Copy an image (Win+Shift+S)\n"
                "2) Click the folder's Explorer window\n"
                "3) Press Ctrl+V\n\n"
                "It lives in the system tray. Right-click the tray icon for "
                "options, or 'Open log' to see what it did.",
                APP_NAME, MB_ICONINFO)

        icon.run()
        keyboard.clear_all_hotkeys()

    except Exception:
        err = traceback.format_exc()
        log_line("FATAL: " + err)
        message_box(
            f"{APP_NAME} could not start.\n\n{err}\n"
            f"A copy of this was written to:\n{LOG_PATH}",
            f"{APP_NAME} error", MB_ICONERROR)


if __name__ == "__main__":
    main()
