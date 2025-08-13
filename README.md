# Stable Diffusion LoRA Organiser (CustomTkinter)

A simple desktop app to catalogue your Stable Diffusion LoRA models, characters, styles, and misc assets.

## Features
- Three categories with separate folders: **Characters**, **Styles**, **Misc** (switch via dropdown)
- Add/Edit entries with:
  - Main preview image (keeps aspect ratio; shortest side scales to 300px)
  - Name, file name, source, model type
  - Any number of **tags** — each tag has an optional **label** (what it's for) and a **value** (click-to-copy button in the viewer)
  - Notes
  - Any number of **additional images** (each with an optional title)
- Catalogue view:
  - Scrollable list of entries on the left
  - Details on the right (tags as copy buttons, notes read-only, images scaled)
  - **DELETE** button with confirmation
- Remembers your last selected category in `app_settings.json`
- Visual cue: background **colour** changes by category (Characters = default dark, Styles = dark red, Misc = dark green)

## Requirements
- Windows/macOS/Linux
- Python 3.10+
- Tkinter (bundled with Python on Windows/macOS; on some Linux distros: `sudo apt install python3-tk`)

## Quick start
### Option A — run directly
```bash
pip install -r requirements.txt
python main.py
```

### Option B — double-click on Windows
Create a file like `START.bat` next to `main.py`:
```bat
@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 ( set PY=python ) else (
  where py >nul 2>nul
  if %errorlevel%==0 ( set PY=py -3 ) else (
    echo Could not find Python. Please install Python 3.10+ and try again.
    pause & exit /b 1
  )
)
%PY% main.py
pause
```

### Option C — auto-venv .bat (recommended for sharing)
```bat
@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 ( set PY=python ) else (
  where py >nul 2>nul
  if %errorlevel%==0 ( set PY=py -3 ) else (
    echo Could not find Python. Please install Python 3.10+ and try again.
    pause & exit /b 1
  )
)
if not exist ".venv" (
  echo Creating virtual environment...
  %PY% -m venv .venv || ( echo Failed to create venv & pause & exit /b 1 )
)
set VENV_PY=".venv\Scripts\python.exe"
if not exist %VENV_PY% ( echo Could not find %VENV_PY% & pause & exit /b 1 )
if exist requirements.txt (
  %VENV_PY% -m pip install --upgrade pip
  %VENV_PY% -m pip install -r requirements.txt
)
%VENV_PY% main.py
pause
```

## Folder layout
The app creates these on first run (alongside the code):
```
Character JSONs/
Style JSONs/
Misc JSONs/
app_settings.json
```
- `app_settings.json` saves your last-used category.
- JSON files are UTF-8.

## JSON example
```json
{
  "name": "Example Character",
  "file_name": "example_char.safetensors",
  "source": "CivitAI",
  "model_type": "Illustrious",
  "tags": [
    {"label": "Camo Outfit", "value": "masterpiece, camo, gritty"},
    {"label": "Pose", "value": "arms crossed"}
  ],
  "notes": "Looks good at 0.65 weight.",
  "image_path": "D:/Images/char_main.png",
  "extra_images": [
    {"title": "Close-up", "image_path": "D:/Images/char_close.png"}
  ]
}
```

## Packaging (optional)
Create a Windows exe with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed main.py
```
Add an icon with `--icon=app.ico` if you have one.

## Troubleshooting
- **Images not showing**: If images were moved/renamed after saving, the viewer will show a placeholder. Edit the entry and update paths.
- **Clipboard oddities on Linux**: Some Wayland setups handle clipboard differently; try running from a terminal or switch to X11 session.
- **Fonts/Theme**: The app uses CustomTkinter’s defaults; you can switch light/dark in `main.py`.

## Licence
MIT — see `LICENSE`.
