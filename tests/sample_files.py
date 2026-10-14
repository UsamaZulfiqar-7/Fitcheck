"""Helpers that build realistic sample CV / job files for the tests."""
import io

CV_TEXT = """Ayesha Khan
Lahore, Pakistan | ayesha@example.com | +92 300 0000000

SUMMARY
Computer science graduate interested in data analysis.

EDUCATION
BS Computer Science, University of Lahore (2020-2024), CGPA 3.8

SKILLS
Python, Excel, Pandas, Data Cleaning, Communication

PROJECTS
- Sales dashboard built with Excel and Python for a local shop
- Student marks analysis using Pandas

EXPERIENCE
Data analysis intern, Example Software House (3 months)
- Cleaned survey data and prepared weekly reports
"""

JOB_TEXT = """Data Analyst

Requirements:
- Strong SQL and Python skills
- Experience with Power BI or Tableau
- Excel and data visualization
- Knowledge of Statistics
- Good communication skills

Nice to have:
- Docker
- Apache Spark
"""


def cv_docx_bytes(text: str = CV_TEXT) -> bytes:
    import docx
    document = docx.Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def text_pdf_bytes(text: str = CV_TEXT) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(40, y, line[:100])
        y -= 14
        if y < 40:
            c.showPage()
            y = 800
    c.save()
    return buf.getvalue()


def text_image_bytes(text: str = JOB_TEXT, fmt: str = "PNG") -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    y = 30
    for line in text.splitlines():
        draw.text((40, y), line, fill="black", font=font)
        y += 48
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def scanned_pdf_bytes(text: str = JOB_TEXT) -> bytes:
    """A PDF that contains only an image (no embedded text) -> needs OCR."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawImage(ImageReader(io.BytesIO(text_image_bytes(text))), 20, 300, width=560, height=360)
    c.save()
    return buf.getvalue()
