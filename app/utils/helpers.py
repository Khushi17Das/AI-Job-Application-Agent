import os
import re
from fastapi import HTTPException, status

def clean_text(text: str) -> str:
    """Removes extra whitespace and cleans raw extracted text."""
    if not text:
        return ""
    # Normalize multiple newlines and spaces
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts plain text from a PDF file.
    Tries PyMuPDF (fitz) first, falls back to pypdf if unavailable.
    """
    text = ""
    # Try PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        if text.strip():
            return clean_text(text)
    except ImportError:
        pass
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")

    # Fallback to pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        if text.strip():
            return clean_text(text)
    except ImportError:
        pass
    except Exception as e:
        print(f"pypdf extraction failed: {e}")

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from the PDF file. Please ensure it contains readable text."
        )
    return clean_text(text)

def extract_text_from_txt(file_path: str) -> str:
    """Reads plain text from a UTF-8 or ASCII encoded TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return clean_text(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read TXT file: {str(e)}"
        )
