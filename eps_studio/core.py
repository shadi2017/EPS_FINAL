"""Rendering and exports independent of the user interface."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import csv
import io
import re
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

def text_value(value):
    return "" if pd.isna(value) else str(value).strip()

def arabic(value):
    return get_display(RESHAPER.reshape(text_value(value)))

def safe_name(value):
    name = re.sub(r'[\x00-\x1f\\/:*?"<>|]', "_", text_value(value)).strip(" .")[:100]
    reserved = {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1,10)], *[f"LPT{i}" for i in range(1,10)]}
    return "record_" + name if not name or name.split(".")[0].upper() in reserved else name

def open_image(source):
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    with Image.open(source) as image:
        return ImageOps.exif_transpose(image).convert("RGBA")

def read_table(data, suffix):
    source = io.BytesIO(data)
    if suffix.lower() == ".csv":
        try:
            frame = pd.read_csv(source, encoding="utf-8-sig", dtype=str)
        except UnicodeDecodeError:
            source.seek(0)
            frame = pd.read_csv(source, encoding="cp1256", dtype=str)
    else:
        frame = pd.read_excel(source, dtype=str)
    return frame.dropna(how="all").reset_index(drop=True).fillna("")

def default_font():
    for path in [ROOT / "assets/fonts/Amiri-Regular.ttf", Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]:
        if path.exists():
            return str(path)
    raise ValueError("Upload a TTF font in layout settings to render your text.")

@lru_cache(maxsize=128)
def font(source, size):
    return ImageFont.truetype(io.BytesIO(source) if isinstance(source, bytes) else source, size)

@dataclass(frozen=True)
class TextStyle:
    x: float = 50
    y: float = 50
    size: int = 100
    color: str = "#17324d"
    width: float = 85

def draw_text(image, value, style, font_source):
    value = arabic(value)
    if not value:
        return
    draw = ImageDraw.Draw(image)
    size = style.size
    face = font(font_source, size)
    max_width = image.width * style.width / 100
    while draw.textbbox((0, 0), value, font=face)[2] > max_width and size > 10:
        size -= 2
        face = font(font_source, size)
    draw.text((image.width*style.x/100, image.height*style.y/100), value, font=face, fill=style.color, anchor="mm")

def render_certificate(template, name, name_style, font_source, grade="", grade_style=None, date="", date_style=None, signature=None, signature_position=(70,80,15)):
    image = template.convert("RGB")
    draw_text(image, name, name_style, font_source)
    if grade_style:
        draw_text(image, grade, grade_style, font_source)
    if date_style:
        draw_text(image, date, date_style, font_source)
    if signature is not None:
        x, y, width = signature_position
        w = max(1, round(image.width*width/100))
        sig = signature.resize((w, max(1, round(signature.height*w/signature.width))), Image.Resampling.LANCZOS)
        image.paste(sig, (round(image.width*x/100), round(image.height*y/100)), sig)
    return image

def prepare_frame(source, clear_center=True, threshold=35):
    image = open_image(source)
    if clear_center and image.getpixel((image.width//2, image.height//2))[3] != 0:
        ImageDraw.floodfill(image, (image.width//2, image.height//2), (0,0,0,0), thresh=threshold)
    return image

def frame_photo(photo, frame, max_edge=0):
    result = photo.copy()
    if max_edge:
        result.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    result.alpha_composite(frame.resize(result.size, Image.Resampling.LANCZOS))
    return result.convert("RGB")

def output_run(parent, prefix):
    path = Path(parent).expanduser() / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:6]}"
    path.mkdir(parents=True, exist_ok=False)
    return path

def write_report(folder, records):
    with (folder / "report.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "status", "output", "error"])
        writer.writeheader()
        writer.writerows(records)

def export_certificates(frame, name_column, renderer, destination, make_pdf=True, quality=95, progress=None):
    from reportlab.pdfgen import canvas
    folder = output_run(destination, "certificates")
    records = []
    pdf = canvas.Canvas(str(folder / "certificates.pdf")) if make_pdf else None
    for i, (_, row) in enumerate(frame.iterrows()):
        name = text_value(row[name_column])
        record = dict(source=name or f"Row {i+1}", status="skipped", output="", error="Name is empty")
        if name:
            try:
                image = renderer(row)
                target = folder / f"{i+1:05d}_{safe_name(name)}.jpg"
                image.save(target, "JPEG", quality=quality, subsampling=0)
                if pdf:
                    w, h = image.size
                    pdf.setPageSize((w*72/150, h*72/150))
                    pdf.drawImage(str(target), 0, 0, width=w*72/150, height=h*72/150)
                    pdf.showPage()
                record.update(status="success", output=target.name, error="")
            except Exception as exc:
                record.update(status="failed", error=str(exc))
        records.append(record)
        if progress:
            progress((i+1)/len(frame))
    if pdf:
        pdf.save()
    write_report(folder, records)
    return folder, records

def export_photos(files, frames, destination, quality=95, max_edge=0, progress=None):
    folder = output_run(destination, "photos")
    records = []
    for i, path in enumerate(files):
        record = dict(source=path.name, status="failed", output="", error="")
        try:
            photo = open_image(path)
            orientation = "landscape" if photo.width > photo.height else "portrait"
            if frames.get(orientation) is None:
                raise ValueError("No frame is available for this photo orientation")
            image = frame_photo(photo, frames[orientation], max_edge)
            target = folder / f"{i+1:05d}_{safe_name(path.stem)}.jpg"
            image.save(target, "JPEG", quality=quality, subsampling=0)
            record.update(status="success", output=target.name)
        except Exception as exc:
            record["error"] = str(exc)
        records.append(record)
        if progress:
            progress((i+1)/len(files))
    write_report(folder, records)
    return folder, records
