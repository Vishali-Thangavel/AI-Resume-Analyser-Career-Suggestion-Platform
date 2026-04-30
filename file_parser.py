"""
file_parser.py – Extract plain text from PDF, DOCX, and TXT uploads.
"""

import io

def parse_file(file_storage) -> str:
    """Accept a Flask FileStorage object; return extracted text."""
    filename = file_storage.filename.lower()
    data = file_storage.read()

    if filename.endswith('.txt'):
        return data.decode('utf-8', errors='ignore')

    if filename.endswith('.pdf'):
        return _parse_pdf(data)

    if filename.endswith('.docx'):
        return _parse_docx(data)

    # Fallback: try UTF-8
    return data.decode('utf-8', errors='ignore')


def _parse_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return '\n'.join(page.extract_text() or '' for page in pdf.pages)
    except ImportError:
        pass

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    except Exception:
        pass

    return "[PDF parsing failed – please paste your resume text instead]"


def _parse_docx(data: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        return '\n'.join(p.text for p in doc.paragraphs)
    except Exception:
        return "[DOCX parsing failed – please paste your resume text instead]"
