"""
GradeOps - Pipeline Orchestrator
Ties together OCR → Grading → Plagiarism Detection → Output
 
Usage:
    python pipeline.py --exams exams/ --rubric rubric.json --out results.json
"""
 
import os
import json
import argparse
from pathlib import Path
from dataclasses import asdict
 
from ocr_pipeline import extract_answers_from_pdf
from grading_agent import (
    QuestionRubric,
    RubricCriterion,
    grade_exam,
    detect_plagiarism,
    annotate_plagiarism,
    GradingResult,
)
 
 
# ── Rubric loader ─────────────────────────────────────────────────────────────
def load_rubric(rubric_path: str):
    """
    Load a JSON rubric file.
 
    Expected JSON format:
    [
      {
        "question_id": "Q1",
        "question_text": "...",
        "total_marks": 10,
        "criteria": [
          {
            "criterion_id": "C1",
            "description": "...",
            "max_marks": 4,
            "keywords": ["keyword1"]
          }
        ]
      }
    ]
    """
    with open(rubric_path) as f:
        data = json.load(f)
 
    rubric_map = {}
    for q in data:
        criteria = [RubricCriterion(**c) for c in q["criteria"]]
        rubric_map[q["question_id"]] = QuestionRubric(
            question_id=q["question_id"],
            question_text=q["question_text"],
            total_marks=q["total_marks"],
            criteria=criteria,
        )
    return rubric_map
 
 
# ── Result serializer ─────────────────────────────────────────────────────────
def result_to_dict(r: GradingResult) -> dict:
    return {
        "question_id": r.question_id,
        "total_awarded": r.total_awarded,
        "max_marks": r.max_marks,
        "percentage": round(r.total_awarded / r.max_marks * 100, 1) if r.max_marks else 0,
        "overall_justification": r.overall_justification,
        "plagiarism_flag": r.plagiarism_flag,
        "plagiarism_note": r.plagiarism_note,
        "criteria_scores": [
            {
                "criterion_id": cs.criterion_id,
                "awarded": cs.awarded,
                "justification": cs.justification,
                "met": cs.met,
            }
            for cs in r.criteria_scores
        ],
    }
 
 
# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(
    exam_dir: str,
    rubric_path: str,
    output_path: str,
    plagiarism_threshold: float = 0.85,
    question_regions=None,
):
    """
    Full GradeOps ML pipeline.
 
    Parameters
    ----------
    exam_dir          : directory of PDF files named <student_id>.pdf
    rubric_path       : path to rubric JSON
    output_path       : path for the output JSON report
    plagiarism_threshold : cosine-similarity threshold for flagging
    question_regions  : optional bounding-box config for page crops
    """
    rubric_map = load_rubric(rubric_path)
    exam_dir_path = Path(exam_dir)
    pdf_files = sorted(exam_dir_path.glob("*.pdf"))
 
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {exam_dir}")
 
    print(f"[GradeOps] Found {len(pdf_files)} exam(s). Starting OCR...")
 
    # Stage 1: OCR all exams
    all_submissions = []   # for plagiarism
    per_student_answers: dict[str, list[dict]] = {}
 
    for pdf_path in pdf_files:
        student_id = pdf_path.stem
        print(f"  → OCR: {student_id}")
        answers = extract_answers_from_pdf(str(pdf_path), question_regions)
        per_student_answers[student_id] = answers
        for ans in answers:
            all_submissions.append({
                "student_id": student_id,
                "question_id": ans["question_id"],
                "raw_text": ans["raw_text"],
            })
 
    print("[GradeOps] OCR complete. Starting grading...")
 
    # Stage 2: Grade all answers
    per_student_results: dict[str, list[GradingResult]] = {}
 
    for student_id, answers in per_student_answers.items():
        print(f"  → Grading: {student_id}")
        results = grade_exam(rubric_map, answers)
        per_student_results[student_id] = results
 
    print("[GradeOps] Grading complete. Running plagiarism detection...")
 
    # Stage 3: Plagiarism detection
    plagiarism_flags = detect_plagiarism(all_submissions, threshold=plagiarism_threshold)
    annotate_plagiarism(per_student_results, plagiarism_flags)
 
    print(f"[GradeOps] Plagiarism check done. {len(plagiarism_flags)} pair(s) flagged.")
 
    # Stage 4: Build output report
    report = {
        "summary": {
            "total_exams": len(pdf_files),
            "plagiarism_pairs_flagged": len(plagiarism_flags),
        },
        "plagiarism_flags": plagiarism_flags,
        "students": {},
    }
 
    for student_id, results in per_student_results.items():
        total_awarded = sum(r.total_awarded for r in results)
        total_possible = sum(r.max_marks for r in results)
        report["students"][student_id] = {
            "total_awarded": total_awarded,
            "total_possible": total_possible,
            "percentage": round(total_awarded / total_possible * 100, 1) if total_possible else 0,
            "questions": [result_to_dict(r) for r in results],
        }
 
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
 
    print(f"[GradeOps] Report saved → {output_path}")
    return report
 
 
# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GradeOps ML Pipeline")
    parser.add_argument("--exams",     required=True, help="Directory of <student_id>.pdf files")
    parser.add_argument("--rubric",    required=True, help="Path to rubric.json")
    parser.add_argument("--out",       default="gradeops_results.json", help="Output report path")
    parser.add_argument("--threshold", type=float, default=0.85, help="Plagiarism similarity threshold")
    parser.add_argument("--regions",   default=None, help="Optional JSON file with page crop regions")
    args = parser.parse_args()
 
    regions = None
    if args.regions:
        with open(args.regions) as f:
            regions = json.load(f)
 
    run_pipeline(
        exam_dir=args.exams,
        rubric_path=args.rubric,
        output_path=args.out,
        plagiarism_threshold=args.threshold,
        question_regions=regions,
    )