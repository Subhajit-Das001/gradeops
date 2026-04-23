"""
GradeOps — OCR Service
Two-tier text extraction:
  1. PyMuPDF get_text() — fast, for digital/typed PDFs
  2. Vision LLM fallback — for scanned/handwritten pages & image files
     (sends page image to Qwen2.5-VL via HF Inference API)
"""

import os
import io
import base64
from pathlib import Path

import fitz  # PyMuPDF
import httpx
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ── Vision model config ──────────────────────────────────────────────────────

HF_TOKEN: str = os.getenv("HF_TOKEN", "")
VISION_MODEL: str = os.getenv("HF_VISION_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct")
HF_API_URL: str = "https://router.huggingface.co/v1/chat/completions"

_VISION_TIMEOUT = 120.0  # Vision models need more time
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


# ── Vision OCR (for scanned / handwritten pages & images) ────────────────────

def _image_to_base64_jpeg(img: Image.Image) -> str:
    """Compress a PIL Image to JPEG and return base64 string."""
    # Resize if too large (keep under ~1MB for fast API response)
    max_dim = 1200
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode()


def _page_to_base64_jpeg(page: fitz.Page, dpi: int = 150) -> str:
    """Render a PDF page to a compressed JPEG base64 string."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return _image_to_base64_jpeg(img)


def _ocr_via_vision(page_b64: str, page_num: int) -> str:
    """
    Send a page image to the vision LLM to extract handwritten text.
    Synchronous call — used inside the sync extract function.
    """
    if not HF_TOKEN:
        return f"[Page {page_num}: No HF_TOKEN — cannot run vision OCR]"

    try:
        resp = httpx.post(
            HF_API_URL,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{page_b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a scanned page from a student exam answer sheet. "
                                "Read and transcribe ALL handwritten and printed text on this page. "
                                "Preserve the structure (question numbers, paragraphs). "
                                "Return ONLY the transcribed text, nothing else."
                            ),
                        },
                    ],
                }],
                "max_tokens": 2048,
                "temperature": 0.1,
            },
            timeout=_VISION_TIMEOUT,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if text:
            return text
        return f"[Page {page_num}: Vision model returned empty text]"

    except httpx.ReadTimeout:
        print(f"[OCR] Vision timeout on page {page_num}")
        return f"[Page {page_num}: Vision OCR timed out]"
    except Exception as e:
        print(f"[OCR] Vision error on page {page_num}: {e}")
        return f"[Page {page_num}: Vision OCR failed — {e}]"


# ── Image file extraction ────────────────────────────────────────────────────

def _extract_from_image(file_path: str) -> list[dict]:
    """Extract text from a standalone image file via vision LLM."""
    try:
        img = Image.open(file_path).convert("RGB")
        b64 = _image_to_base64_jpeg(img)
        print(f"[OCR] Image file: sending to vision OCR…")
        text = _ocr_via_vision(b64, page_num=1)
        print(f"[OCR] Image file: vision extracted {len(text)} chars")
        return [{"question_id": "Q1", "page": 0, "raw_text": text}]
    except Exception as e:
        print(f"[OCR] Error processing image {file_path}: {e}")
        return [{"question_id": "Q1", "page": 0, "raw_text": "Extraction failed."}]


# ── PDF extraction ───────────────────────────────────────────────────────────

def _extract_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from each page of a PDF.
    Tier 1: PyMuPDF get_text() for digital text.
    Tier 2: Vision LLM for scanned/handwritten pages.
    """
    results = []
    try:
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            page_num = i + 1

            # Tier 1: Fast text extraction
            text = page.get_text().strip()

            if text:
                print(f"[OCR] Page {page_num}: extracted {len(text)} chars (digital text)")
            else:
                # Tier 2: Vision LLM for scanned/handwritten pages
                print(f"[OCR] Page {page_num}: no digital text — using vision OCR…")
                page_b64 = _page_to_base64_jpeg(page)
                text = _ocr_via_vision(page_b64, page_num)
                print(f"[OCR] Page {page_num}: vision extracted {len(text)} chars")

            results.append({
                "question_id": f"Q{page_num}",
                "page": i,
                "raw_text": text,
            })
        doc.close()
    except Exception as e:
        print(f"[OCR] Error processing PDF {file_path}: {e}")
        results = [{"question_id": "Q1", "page": 0, "raw_text": "Extraction failed."}]

    return results


# ── Main entry point ─────────────────────────────────────────────────────────

def extract_text_from_file(file_path: str) -> list[dict]:
    """
    Extract text from a PDF or image file.

    Supports: .pdf, .jpg, .jpeg, .png, .bmp, .tiff, .webp

    Returns
    -------
    List of {"question_id": "Q1", "page": 0, "raw_text": "…"}
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in _IMAGE_EXTENSIONS:
        return _extract_from_image(file_path)
    else:
        print(f"[OCR] Unsupported file type: {ext}")
        return [{"question_id": "Q1", "page": 0, "raw_text": f"Unsupported file type: {ext}"}]
