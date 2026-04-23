"""
GradeOps — Grading Pipeline
Orchestrates: OCR → Q&A Splitting → AI Grading → DB Save
"""

import asyncio
from collections import defaultdict

import models
from database import SessionLocal
from ocr_service import extract_text_from_file
from llm_service import split_text_to_answers, grade_answer


async def _run_pipeline(script_id: int) -> None:
    """
    Full async grading pipeline for a single student script.

    Steps:
        1. Extract text from uploaded PDF  (local PyMuPDF)
        2. Split text into per-question answers  (remote LLM)
        3. Grade each question against its rubric criteria  (remote LLM)
        4. Save results to the database
    """
    db = SessionLocal()
    try:
        script = (
            db.query(models.StudentScript)
            .filter(models.StudentScript.id == script_id)
            .first()
        )
        if not script or not script.rubric_id:
            print(f"[Pipeline] No rubric for script {script_id}, skipping.")
            return

        rubric = (
            db.query(models.Rubric)
            .filter(models.Rubric.id == script.rubric_id)
            .first()
        )
        if not rubric:
            print(f"[Pipeline] Rubric not found for script {script_id}.")
            return

        # ── Step 1: Extract text ──────────────────────────────────────────
        print(f"[Pipeline] Extracting text from {script.filename}…")
        ocr_results = extract_text_from_file(script.file_path)
        full_text = "\n\n".join(r["raw_text"] for r in ocr_results)

        # ── Step 2: Group criteria by question ────────────────────────────
        criteria_by_question: dict[str, list] = defaultdict(list)
        for c in rubric.criteria:
            criteria_by_question[c.question_id].append(c)

        # Build unique question list for the splitter
        unique_questions = [
            {"id": qid, "text": clist[0].question_text}
            for qid, clist in criteria_by_question.items()
        ]

        # ── Step 3: Split text into per-question answers ──────────────────
        print(f"[Pipeline] Splitting answers for {len(unique_questions)} question(s)…")
        answer_map = await split_text_to_answers(full_text, unique_questions)

        # Fallback: assign full text if splitter failed
        if not answer_map:
            answer_map = {q["id"]: full_text for q in unique_questions}

        # ── Step 4: Grade each question ───────────────────────────────────
        for qid, criteria in criteria_by_question.items():
            # Skip if already graded
            existing = (
                db.query(models.GradingResult)
                .filter(
                    models.GradingResult.script_id == script_id,
                    models.GradingResult.question_id == qid,
                )
                .first()
            )
            if existing:
                continue

            student_answer = answer_map.get(qid, "No answer found.")
            question_text = criteria[0].question_text
            total_possible = sum(c.max_marks for c in criteria)

            print(f"[Pipeline] Grading {qid} via remote LLM…")
            ai_result = await grade_answer(qid, question_text, criteria, student_answer)

            # Save grading result
            gr = models.GradingResult(
                script_id=script.id,
                question_id=qid,
                total_awarded=min(float(ai_result.get("total_awarded", 0)), total_possible),
                max_marks=total_possible,
                overall_justification=ai_result.get("overall_justification", ""),
                plagiarism_flag=False,
            )
            db.add(gr)
            db.flush()

            # Save per-criterion scores
            for cs in ai_result.get("criteria_scores", []):
                max_m = next(
                    (c.max_marks for c in criteria if c.criterion_id == cs.get("criterion_id")),
                    0,
                )
                db.add(models.CriterionScore(
                    grading_result_id=gr.id,
                    criterion_id=cs.get("criterion_id", ""),
                    awarded=min(float(cs.get("awarded", 0)), max_m),
                    justification=cs.get("justification", ""),
                    met=bool(cs.get("met", False)),
                ))

        script.status = "graded"
        db.commit()
        print(f"[Pipeline] Done grading script {script_id} ({script.student_roll}) ✓")

    except Exception as e:
        print(f"[Pipeline] ERROR on script {script_id}: {e}")
        db.rollback()
    finally:
        db.close()


def run_grading_for_script(script_id: int) -> None:
    """
    Sync wrapper for the async pipeline.
    Safe to call from FastAPI BackgroundTasks and from startup hooks.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're already inside an event loop (e.g. FastAPI background task)
        # Create a new task instead
        asyncio.ensure_future(_run_pipeline(script_id))
    else:
        asyncio.run(_run_pipeline(script_id))
