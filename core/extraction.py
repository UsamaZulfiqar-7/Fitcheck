"""Text extraction from CVs and job postings.

Order of preference: embedded PDF text -> OCR (scanned PDFs / images only when needed).
Every failure is converted into an `ExtractionError` with a user-friendly message.
"""
from __future__ import annotations

import io
import os
import re
import zipfile
from dataclasses import dataclass, field

import config

RESUME_TYPES = ["pdf", "docx", "txt"]
JOB_TYPES = ["pdf", "jpg", "jpeg", "png", "txt"]
IMAGE_TYPES = {"jpg", "jpeg", "png"}

OCR_HELP = (
    "OCR needs the free Tesseract program.\n"
    "Windows: install it from https://github.com/UB-Mannheim/tesseract/wiki (default path "
    "C:\\Program Files\\Tesseract-OCR), then either add that folder to PATH or set "
    "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe in your .env file and restart the app."
)

_WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class ExtractionError(Exception):
    """Raised with a message that can be shown directly to the user."""


@dataclass
class ExtractionResult:
    text: str
    method: str
    warnings: list[str] = field(default_factory=list)
    pages: int = 0


# ---- helpers ---------------------------------------------------------------------
def file_extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower().lstrip(".")


def clean_text(text: str) -> str:
    text = (text or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_upload(filename: str, data: bytes, allowed: list[str]) -> str:
    ext = file_extension(filename)
    if not data:
        raise ExtractionError("The file is empty. Please upload a file that has content.")
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise ExtractionError(f"The file is larger than {config.MAX_UPLOAD_MB} MB. Please upload a smaller file.")
    if ext not in allowed:
        raise ExtractionError(f"Unsupported file type '.{ext}'. Allowed: {', '.join(t.upper() for t in allowed)}.")
    if ext == "pdf" and not data.lstrip().startswith(b"%PDF"):
        raise ExtractionError("This file has a .pdf extension but is not a valid PDF.")
    if ext == "docx" and not zipfile.is_zipfile(io.BytesIO(data)):
        raise ExtractionError("This file has a .docx extension but is not a valid Word document.")
    return ext


def ocr_available() -> bool:
    try:
        import pytesseract

        cmd = config.TESSERACT_CMD or (_WINDOWS_TESSERACT if os.path.exists(_WINDOWS_TESSERACT) else "")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ocr_image(image) -> str:
    if not ocr_available():
        raise ExtractionError("This file needs OCR (text recognition), but Tesseract was not found.\n" + OCR_HELP)
    import pytesseract
    from PIL import ImageOps

    image = ImageOps.grayscale(image)
    if image.width < 1200:                       # small images OCR badly; upscale
        ratio = 1200 / max(image.width, 1)
        image = image.resize((int(image.width * ratio), int(image.height * ratio)))
    return pytesseract.image_to_string(image)


# ---- format readers -------------------------------------------------------------------
def _read_pdf(data: bytes) -> ExtractionResult:
    import pdfplumber

    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("The PDF could not be opened. It may be damaged or password-protected.") from exc
    warnings: list[str] = []
    with pdf:
        pages = len(pdf.pages)
        parts = [(page.extract_text() or "") for page in pdf.pages]
        text = clean_text("\n".join(parts))
        if len(text) >= 40:
            return ExtractionResult(text, "embedded PDF text", warnings, pages)
        # scanned PDF -> OCR first pages
        ocr_parts = []
        for page in pdf.pages[: config.OCR_MAX_PAGES]:
            ocr_parts.append(_ocr_image(page.to_image(resolution=200).original))
        if pages > config.OCR_MAX_PAGES:
            warnings.append(f"Only the first {config.OCR_MAX_PAGES} pages were read with OCR.")
        warnings.append("This PDF looks scanned, so OCR was used. Please review the text for mistakes.")
        return ExtractionResult(clean_text("\n".join(ocr_parts)), "OCR (scanned PDF)", warnings, pages)


def _read_docx(data: bytes) -> ExtractionResult:
    import docx

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("The Word document could not be read. It may be damaged.") from exc
    lines: list[str] = []
    try:
        blocks = list(document.iter_inner_content())
    except AttributeError:                      # older python-docx
        blocks = list(document.paragraphs) + list(document.tables)
    for block in blocks:
        if hasattr(block, "rows"):               # table
            for row in block.rows:
                cells = []
                for cell in row.cells:
                    value = cell.text.strip()
                    if value and value not in cells:
                        cells.append(value)
                if cells:
                    lines.append(" | ".join(cells))
        else:
            lines.append(block.text)
    return ExtractionResult(clean_text("\n".join(lines)), "Word document text", [], 1)


def _read_txt(data: bytes) -> ExtractionResult:
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return ExtractionResult(clean_text(data.decode(encoding)), "plain text", [], 1)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ExtractionError("The text file could not be decoded.")


def _read_image(data: bytes) -> ExtractionResult:
    from PIL import Image

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise ExtractionError("The image could not be opened. Please upload a valid JPG or PNG.") from exc
    text = clean_text(_ocr_image(image))
    return ExtractionResult(text, "OCR (image)", ["Text was read with OCR. Please review it for mistakes."], 1)


# ---- public API --------------------------------------------------------------------
def extract_text(data: bytes, filename: str, allowed: list[str]) -> ExtractionResult:
    ext = validate_upload(filename, data, allowed)
    if ext == "pdf":
        result = _read_pdf(data)
    elif ext == "docx":
        result = _read_docx(data)
    elif ext == "txt":
        result = _read_txt(data)
    else:
        result = _read_image(data)
    if len(result.text) < 20:
        raise ExtractionError("Almost no text could be read from this file. "
                              "If it is a scan or photo, use a clearer/higher-resolution version, "
                              "or paste the text manually.")
    return result
