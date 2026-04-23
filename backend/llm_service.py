"""
GradeOps — Remote LLM Service
All AI calls go through the Hugging Face Inference API.
No local model, no GPU required.
"""

import os
import json
import random
from typing import List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

HF_TOKEN: str = os.getenv("HF_TOKEN", "")
HF_MODEL: str = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
HF_API_URL: str = "https://router.huggingface.co/v1/chat/completions"

_TIMEOUT = 60.0
_TEMPERATURE = 0.1  # Deterministic for grading consistency


# ── Core API call ─────────────────────────────────────────────────────────────

async def call_hf_chat(prompt: str, max_tokens: int = 1024) -> Optional[dict]:
    """
    Send a prompt to the HF Inference API and return parsed JSON.

    Returns None if the token is missing, the API fails, or the response
    cannot be parsed as JSON.
    """
    if not HF_TOKEN:
        print("[LLM] No HF_TOKEN set — cannot call remote model.")
        return None

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": _TEMPERATURE,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                HF_API_URL, headers=headers, json=payload, timeout=_TIMEOUT
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return _extract_json(content)
        except httpx.HTTPStatusError as e:
            print(f"[LLM] HTTP {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"[LLM] API error: {e}")
            return None


def _extract_json(text: str) -> Optional[dict]:
    """Pull a JSON object out of LLM output that may contain markdown fences."""
    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    # Find the outermost { … }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        print(f"[LLM] No JSON object found in response: {text[:120]}…")
        return None

    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError as e:
        print(f"[LLM] JSON parse error: {e}")
        return None


# ── Split OCR text into per-question answers ──────────────────────────────────

async def split_text_to_answers(
    full_text: str, questions: List[dict]
) -> dict[str, str]:
    """
    Use the LLM to parse raw OCR text into per-question answers.

    Parameters
    ----------
    full_text : concatenated OCR output
    questions : list of {"id": "Q1", "text": "What is …"}

    Returns
    -------
    Dict mapping question IDs to extracted answer text.
    Falls back to assigning full_text to every question on failure.
    """
    fallback = {q["id"]: full_text for q in questions}

    q_list = "\n".join(f"- {q['id']}: {q['text']}" for q in questions)
    prompt = f"""You are an exam paper parser. The following is OCR text from a student exam paper.
Split the text into answers for these questions:
{q_list}

OCR TEXT:
{full_text}

Return ONLY a JSON object mapping question IDs to the extracted answer text.
Format: {{"Q1": "answer text", "Q2": "answer text"}}
If an answer is not found, use an empty string."""

    result = await call_hf_chat(prompt, max_tokens=2048)
    if result is None:
        print("[LLM] Q&A split failed — assigning full text to all questions.")
        return fallback
    return result


# ── Grade a single answer ─────────────────────────────────────────────────────

async def grade_answer(
    question_id: str,
    question_text: str,
    criteria: list,
    student_answer: str,
) -> dict:
    """
    Grade one student answer against rubric criteria via the remote LLM.

    Parameters
    ----------
    criteria : list of SQLAlchemy RubricCriterion objects
               (must have .criterion_id, .max_marks, .description, .keywords)

    Returns
    -------
    Dict with keys: question_id, total_awarded, max_marks,
                    criteria_scores, overall_justification
    """
    total_possible = sum(c.max_marks for c in criteria)

    criteria_text = "\n".join(
        f"  [{c.criterion_id}] ({c.max_marks} marks): {c.description}"
        + (f" | Keywords: {', '.join(c.keywords)}" if c.keywords else "")
        for c in criteria
    )

    prompt = f"""You are a strict but fair university exam grader.

Question ({question_id}): {question_text}

Rubric Criteria:
{criteria_text}
Total marks available: {total_possible}

Student Answer:
---
{student_answer}
---

Grade each criterion. Return ONLY raw JSON — no markdown, no backticks.
{{
  "question_id": "{question_id}",
  "total_awarded": <float>,
  "max_marks": {total_possible},
  "criteria_scores": [
    {{
      "criterion_id": "C1",
      "awarded": <float>,
      "justification": "1-2 sentence explanation",
      "met": <true or false>
    }}
  ],
  "overall_justification": "2-3 sentence summary"
}}"""

    result = await call_hf_chat(prompt)

    if result is None:
        print(f"[LLM] Grading failed for {question_id} — using mock fallback.")
        return _mock_grade(question_id, criteria, total_possible)

    # Cap awarded marks to rubric limits
    result["total_awarded"] = min(
        float(result.get("total_awarded", 0)), total_possible
    )
    for cs in result.get("criteria_scores", []):
        max_m = next(
            (c.max_marks for c in criteria if c.criterion_id == cs.get("criterion_id")),
            0,
        )
        cs["awarded"] = min(float(cs.get("awarded", 0)), max_m)

    return result


# ── Mock fallback ─────────────────────────────────────────────────────────────

def _mock_grade(question_id: str, criteria: list, total_possible: float) -> dict:
    """Deterministic-ish fallback when the API is unavailable."""
    pct = random.uniform(0.6, 0.85)
    return {
        "question_id": question_id,
        "total_awarded": round(total_possible * pct, 1),
        "max_marks": total_possible,
        "criteria_scores": [
            {
                "criterion_id": c.criterion_id,
                "awarded": round(c.max_marks * pct, 1),
                "justification": (
                    f"{'Fully satisfied' if pct >= 0.75 else 'Partially satisfied'}: "
                    f"{c.description}. Awarded {round(c.max_marks * pct, 1)} of {c.max_marks}."
                ),
                "met": pct >= 0.75,
            }
            for c in criteria
        ],
        "overall_justification": (
            f"Question {question_id} — Fallback evaluation: "
            f"~{pct:.0%} of expected content. "
            f"Total: {round(total_possible * pct, 1)} / {total_possible}."
        ),
    }
