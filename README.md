# EPS Studio

A local production workspace for batch certificates and framed photos. All application controls, messages, and reports use English. Arabic text in your source data remains supported and is rendered without translating it.

## Start on Windows

1. Install Python 3.12 and add it to PATH.
2. Run `setup_eps.bat` once to install the project environment. Setup requires internet access.
3. Run `run_eps.bat`, or use `EPS_Launch.vbs` for a hidden console.

After setup, processing runs locally without downloading fonts or uploading your files. Windows Arial is the default font; upload a TTF/OTF file to use another font. Run setup again on a new computer instead of copying `.venv`.

## Certificate Studio

- Select a library template or upload an image. Upload Excel/CSV data or select a project data file.
- Excel reads the first worksheet. CSV supports UTF-8 and Windows Arabic encoding. Text values and CSV leading zeros are preserved.
- Select the student name column. Position text using percentages of template dimensions.
- Long names shrink to fit the chosen width, down to a minimum font size of 10.
- Optionally include a grade, date, transparent PNG signature, or custom font.
- Preview any record and download a sample before exporting the batch.
- Saved text layouts include positions, font sizes, colors, and text widths. Select your source files, columns, signature, and custom font for each session.
- Export individual JPEG files and an optional combined PDF. PDF page dimensions use 150 DPI; pages contain certificate images rather than editable text.

## Photo Studio

- Select a source folder. Only its direct image files are processed, not subfolders.
- `frame_land.png` handles landscape photos; `frame_port.png` handles portrait and square photos. Optional uploads override either frame.
- Center-background removal clears the color connected to the center. It can affect design elements connected to that background; review the preview. Turn it off for transparent frames.
- EXIF orientation is corrected before selecting a frame.
- Frames stretch to the photo dimensions. Match frame and photo aspect ratios to avoid stretching logos.
- Preserve original resolution or choose a maximum edge length. Outputs are always JPEG files with a `.jpg` extension.

## Output protection

Every export creates a separate folder inside the selected output directory. Numbered filenames prevent collisions, and original images are not overwritten. Missing names are skipped. A corrupt image does not stop the rest of the batch. Each `report.csv` records the status and error for every item.

Disk or permission failures can leave a partial batch. Review the error and exported files before retrying.

## Project structure

```text
app.py                         Application entry point
eps_studio/core.py             File reading, rendering, and batch exports
eps_studio/ui.py               Navigation and visual theme
eps_studio/certificates_ui.py   Certificate workspace
eps_studio/photos_ui.py         Photo workspace
eps_studio/shared_ui.py         Shared controls and cached resources
tests/test_core.py             Processing regression tests
.streamlit/config.toml         Theme and local server settings
requirements.txt               Tested dependency versions
app_legacy.py.bak               Original application backup
Cert_Out/                      Certificate exports
Img_Out/                       Photo exports
```

The processing engine is independent of Streamlit. File reads, frame preparation, and fonts use bounded caches. PDF generation reuses exported JPEG files instead of retaining all uncompressed certificate images.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Performance depends on image dimensions, batch size, and disk speed. No comprehensive before-and-after benchmark has been performed.
