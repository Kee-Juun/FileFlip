# FileFlip

FileFlip is a PyQt6 desktop utility for batch-converting PDF, Word, and raster
image files through a compact, format-aware interface.

## Run

```powershell
python -B main.py
```

The project now follows the same broad layout as the MOADMN Collector app:
configuration, core logic, UI, and utilities each have their own top-level
package.

## Project Layout

- `main.py` is the thin root entrypoint.
- `config/` stores app metadata and UI defaults.
- `core/` contains conversion services, compatibility patches, and data models.
- `ui/` contains the Qt window, background worker, theme skins, and dialogs.
- `utils/` contains logging and desktop integration helpers.

## Behavior

- Two smart **From** and **To** selectors replace the old single mode menu. The
  destination list automatically shows only routes supported by the selected
  source family. FileFlip restores the last selected route on the next launch.
- PDF to Word uses `pdf2docx`.
- If normal PDF to Word conversion fails, FileFlip tries a text-only Tesseract
  OCR fallback. It checks the same places as the collector/autorouter tools:
  `FILEFLIP_TESSERACT_PATH`, PATH, Program Files, bundled `tesseract` folders,
  and bundled `assets/tesseract` folders.
- Word to PDF uses Microsoft Word automation on Windows and requires Word to be
  installed. Word is kept open for the batch so first-launch COM cleanup does
  not falsely fail converted files.
- PDF pages can be rendered to PNG, JPG, or TIFF. Multipage PDF output becomes
  one numbered-file folder for PNG/JPG and one multipage file for TIFF.
- PNG, JPG/JPEG, TIFF, WebP, BMP, and GIF inputs can be converted to PDF, PNG,
  JPG, TIFF, WebP, or BMP. Animated and multipage inputs are preserved in PDF,
  TIFF, and WebP; single-frame targets are written to a numbered-file folder.
- DPI controls PDF rendering and image-to-PDF resolution. Quality controls JPG
  and WebP compression. These options appear only when the chosen route uses
  them.
- Transparent pixels are flattened onto white for output formats that do not
  support alpha, including JPG, BMP, and PDF.
- Conversion runs in a background Qt thread so the interface stays responsive.
- The interface is intentionally compact: add files, choose output behavior, and
  convert from one main screen. The detailed log stays hidden behind **Details**.
- Successful batches reset the queue and progress bar after the completion
  prompt. Failed or cancelled batches keep their rows visible for review.
- Light, Dark, Coffee, and Vibrant themes are available from the secondary
  **Skin** control in the options toolbar, keeping the **From** and **To**
  selectors visually prominent. Each
  theme uses an integrated skin with soft color panels and one header font from
  `assets/`; Coffee uses Fraunces and Vibrant uses Pacifico. FileFlip remembers
  the last selected theme and restores it on the next launch.
- The window is frameless with a custom title bar and themed resize handle.
- Existing output files are preserved by default. Enable **Overwrite existing
  files** to replace them.
- **Delete originals** removes each source only after that file has converted
  successfully. It is off by default; failed and unprocessed files are always
  kept.
- **Save log** controls whether a text log is written. It is on by default and
  saves to the selected output folder or the first source folder when using
  source folders. Log filenames use the `fileflip-log_` prefix.
- Checkbox preferences, image DPI, and image quality are saved immediately and
  restored the next time FileFlip starts.

## Development Checks

```powershell
python -B -m compileall -q main.py config core ui utils
python -B -m unittest discover -s tests -v
```

For a headless UI smoke test:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -c "from PyQt6.QtWidgets import QApplication; from ui.gui import MainWindow; app=QApplication([]); w=MainWindow(); print(w.windowTitle())"
```

Regenerate the premium PNG and multi-size Windows icon after changing
`ui/icons.py`:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B tools/export_icon.py
```

## Package

Use the spec file when you want Tesseract bundled with the app:

```powershell
python -m PyInstaller FileFlip.spec --clean
```

The spec builds a windowed `FileFlip.exe` and includes `assets/` plus
`C:\Program Files\Tesseract-OCR` as the bundled `tesseract` folder. The exe will
be larger, and first launch may be slower because Tesseract is unpacked before
OCR can run.
