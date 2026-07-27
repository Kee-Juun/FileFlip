# FileFlip Architecture

FileFlip is intentionally organized like the collector apps: a thin entrypoint,
domain code in `core`, UI code in `ui`, shared helpers in `utils`, and static
application defaults in `config`.

## Module Map

- `main.py` starts the app by calling `ui.gui.run_app()`.
- `config/settings.py` stores app name, version, organization, and window sizes.
- `core/models.py` defines conversion modes, options, results, and batch summary
  objects used by the UI and worker.
- `core/converter.py` owns all conversion and output filename behavior.
- `core/image_conversion.py` renders PDF pages and handles raster-image output,
  including animated and multipage inputs.
- `core/compat.py` contains compatibility patches needed by third-party PDF
  tooling.
- `core/ocr.py` owns the optional Tesseract OCR fallback for PDFs that the
  normal converter cannot finish.
- `core/word_pdf.py` owns the managed Microsoft Word session used for DOCX to
  PDF exports on Windows.
- `ui/gui.py` builds the compact PyQt6 interface and wires user actions.
- `ui/dialogs.py` provides theme-aware prompts and completion messages.
- `ui/decorations.py` paints integrated theme skins, header art, and accent
  rules.
- `ui/fonts.py` loads bundled theme fonts from `assets/`.
- `ui/icons.py` generates the app icon from the Vibrant title-bar badge style.
- `ui/titlebar.py` provides the custom frameless title bar and resize handle.
- `ui/worker.py` runs conversion batches on a background `QThread`.
- `ui/themes.py` defines Light, Dark, Coffee, and Vibrant theme palettes.
- `utils/logger.py` writes timestamped batch logs.
- `utils/platform.py` handles OS-specific file manager integration.

## UI Themes

The secondary **Skin** selector is in the options toolbar, away from the primary
**From** and **To** controls. FileFlip includes Light, Dark, Coffee, and Vibrant
themes. Each theme uses an integrated skin: a soft app background,
subtle top-right header art, and one clean accent rule, rather than scattered
decorative widgets. Each theme also uses its own header font from `assets/`.
Coffee uses Fraunces for a warmer cafe-style display face, while Vibrant uses
Pacifico for a more flowing, energetic title.
`ui/themes.py` keeps color palettes and stylesheet generation in one place,
while `ui/decorations.py` paints the theme skin surfaces.

## Conversion Flow

1. `ui.gui.MainWindow` uses smart **From** and **To** selectors to expose only
   supported routes, then gathers the selected files and options.
2. `ui.worker.ConversionWorker` receives immutable `ConversionOptions`.
3. `core.converter.DocumentConverter` converts one file at a time.
4. PDF to Word uses `pdf2docx` first. If that fails, `core.ocr` tries a
   text-only Tesseract fallback and writes a DOCX from recognized page text.
5. For Word to PDF batches, `core.word_pdf.WordToPdfSession` starts Word once,
   exports every DOCX, closes each document, and quits Word during final cleanup.
6. `core.image_conversion` handles PDF to PNG/JPG/TIFF and raster image to
   PDF/PNG/JPG/TIFF/WebP/BMP, with multipage-safe outputs.
7. The worker optionally deletes each source after its conversion succeeds.
8. `utils.logger.SessionLog` records progress and optionally writes the final
   log file.
9. The worker emits progress, row results, and a final `BatchSummary` back to
   the UI thread.
