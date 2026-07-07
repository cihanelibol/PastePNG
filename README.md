# PastePNG

PastePNG does not collect or send any data.

Windows won't let you paste a clipboard image into a folder as a file. You copy a screenshot with Win+Shift+S, open Explorer, press Ctrl+V, and nothing happens. The usual workaround is to open Paint, paste, and save. PastePNG skips all that.

Copy an image, click the Explorer window you want, press Ctrl+V. The image lands in that folder as a PNG. That's the whole tool.

## How it works

PastePNG sits in the system tray. When you press Ctrl+V it checks two things: whether an Explorer window is focused, and whether the clipboard holds an image. If both are true, it writes the image into that folder as `Screenshot.png` (then `Screenshot (1).png`, and so on). Every other time, Ctrl+V behaves exactly as it always did, so pasting text or files anywhere else is untouched.

## Install

Download the latest `PastePNG.exe` from the [Releases](../../releases) page and run it. No Python required.

Run from source instead:

```
pip install -r requirements.txt
python pastepng.py
```

Build your own exe:

```
pip install pyinstaller
pyinstaller pastepng.spec
```

The result is `dist/PastePNG.exe`, a single windowless file.

## First launch

When you run it by hand, a small dialog confirms it started and reminds you of the three steps. If something goes wrong at startup, a dialog shows the error and writes it to the log. Launching a second copy just tells you it's already running. When Windows starts it at login, it stays silent and goes straight to the tray.

## Tray menu

`Enabled` pauses or resumes the tool without quitting. `Start with Windows` launches it at login. `Open log` shows a running record of what each Ctrl+V did, which is the quickest way to confirm it's saving. `Quit` closes it.

## Settings

The constants at the top of `pastepng.py` control the behavior. `HOTKEY` defaults to `ctrl+v`; set it to `ctrl+alt+v` if you'd rather keep the paste key to itself. `BASE_NAME` is the file name it writes, and `EXT` is the extension.

## Limitations

PastePNG only writes to real folders, so it skips locations like This PC or the navigation tree that have no path on disk. If the focused window is running as administrator, PastePNG has to run as administrator too, because Windows blocks keyboard hooks across that boundary.

## License

MIT. See [LICENSE](LICENSE).
