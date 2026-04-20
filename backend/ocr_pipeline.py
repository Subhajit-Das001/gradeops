
"""
GradeOps - OCR Pipeline
Uses Hugging Face Nougat / Qwen-VL to extract handwritten answers from exam scans.
"""
 
import os
import json
import base64
from pathlib import Path
from typing import Union
from PIL import Image
import torch
from transformers import (
    NougatProcessor,
    VisionEncoderDecoderModel,
    AutoProcessor,
    Qwen2VLForConditionalGeneration,
)
import fitz  # PyMuPDF
 
 
# ── Config ──────────────────────────────────────────────────────────────────
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OCR_MODEL = os.getenv("OCR_MODEL", "qwen")   # "nougat" | "qwen"
 
NOUGAT_CKPT  = "facebook/nougat-base"
QWEN_VL_CKPT = "Qwen/Qwen2-VL-7B-Instruct"
 
 
# ── PDF → Image pages ────────────────────────────────────────────────────────
def pdf_to_images(pdf_path: str, dpi: int = 200):
    """Render every page of a PDF as a PIL Image."""
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images
 
 
# ── Nougat OCR ───────────────────────────────────────────────────────────────
class NougatOCR:
    """Lightweight academic-document OCR (good for printed / semi-structured)."""
 
    def __init__(self):
        self.processor = NougatProcessor.from_pretrained(NOUGAT_CKPT)
        self.model = VisionEncoderDecoderModel.from_pretrained(
            NOUGAT_CKPT, torch_dtype=torch.float16
        ).to(DEVICE)
        self.model.eval()
 
    @torch.inference_mode()
    def transcribe(self, image: Image.Image) -> str:
        inputs = self.processor(image, return_tensors="pt").to(DEVICE)
        ids = self.model.generate(
            **inputs,
            min_length=1,
            max_new_tokens=1024,
            bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )
        text = self.processor.batch_decode(ids.sequences, skip_special_tokens=True)[0]
        return self.processor.post_process_generation(text, fix_markdown=True)
 
 
# ── Qwen-VL OCR ──────────────────────────────────────────────────────────────
class QwenVLOCR:
    """Multimodal VLM — handles messy handwriting and layout."""
 
    SYSTEM_PROMPT = (
        "You are an expert OCR assistant for handwritten university exam papers. "
        "Transcribe the answer written in the image EXACTLY. "
        "Preserve paragraph structure. Return only the transcribed text, nothing else."
    )
 
    def __init__(self):
        self.processor = AutoProcessor.from_pretrained(QWEN_VL_CKPT, trust_remote_code=True)
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            QWEN_VL_CKPT,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        self.model.eval()
 
    @torch.inference_mode()
    def transcribe(self, image: Image.Image) -> str:
        # Convert image to base64 for the chat template
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
 
        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": f"data:image/png;base64,{b64}"},
                    {"type": "text",  "text": "Transcribe the handwritten answer above."},
                ],
            },
        ]
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=[text],
            images=[image],
            padding=True,
            return_tensors="pt",
        ).to(DEVICE)
 
        ids = self.model.generate(**inputs, max_new_tokens=1024)
        # Strip the prompt tokens
        new_ids = [ids[i][len(inputs.input_ids[i]):] for i in range(len(ids))]
        return self.processor.batch_decode(new_ids, skip_special_tokens=True)[0].strip()
 
 
# ── Factory ───────────────────────────────────────────────────────────────────
def get_ocr_model():
    if OCR_MODEL == "qwen":
        return QwenVLOCR()
    return NougatOCR()
 
 
# ── High-level extraction API ─────────────────────────────────────────────────
def extract_answers_from_pdf(
    pdf_path: str,
    question_regions=None,
):
    """
    Parameters
    ----------
    pdf_path : str
        Path to the scanned exam PDF.
    question_regions : list of dicts (optional)
        Each dict: {"page": 0, "bbox": [x0, y0, x1, y1], "question_id": "Q1"}
        If None, treats each whole page as one answer region.
 
    Returns
    -------
    list of dicts: [{"question_id": ..., "page": ..., "raw_text": ...}, ...]
    """
    ocr = get_ocr_model()
    pages = pdf_to_images(pdf_path)
    results = []
 
    if question_regions is None:
        # One answer per page
        for i, img in enumerate(pages):
            text = ocr.transcribe(img)
            results.append({"question_id": f"Q{i+1}", "page": i, "raw_text": text})
    else:
        for region in question_regions:
            page_img = pages[region["page"]]
            # Crop to bounding box if provided
            if "bbox" in region:
                x0, y0, x1, y1 = region["bbox"]
                cropped = page_img.crop((x0, y0, x1, y1))
            else:
                cropped = page_img
            text = ocr.transcribe(cropped)
            results.append({
                "question_id": region["question_id"],
                "page": region["page"],
                "raw_text": text,
            })
 
    return results
 
 
# ── CLI demo ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else "exam_sample.pdf"
    out = extract_answers_from_pdf(pdf)
    print(json.dumps(out, indent=2))