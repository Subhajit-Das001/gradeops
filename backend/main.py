"""
GradeOps — FastAPI Backend
Clean, modular API server.
- OCR via PyMuPDF (local, lightweight)
- Grading via Hugging Face Inference API (remote, no GPU)
"""

import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI, HTTPException, Depends,
    File, UploadFile, Form, BackgroundTasks, Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

import models
from database import engine, get_db, SessionLocal
from grading_pipeline import run_grading_for_script

load_dotenv()


# ── Lifespan: auto-grade pending scripts on startup ──────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Grade any scripts that were left in 'pending' state."""
    db = SessionLocal()
    try:
        pending = (
            db.query(models.StudentScript)
            .filter(
                models.StudentScript.status == "pending",
                models.StudentScript.rubric_id != None,
            )
            .all()
        )
        for s in pending:
            print(f"[GradeOps] Auto-grading pending script {s.id} ({s.student_roll})")
            run_grading_for_script(s.id)
    finally:
        db.close()
    yield


# ── App initialisation ───────────────────────────────────────────────────────

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GradeOps API", version="2.0.0", lifespan=lifespan)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str
    dept_code: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class CriterionIn(BaseModel):
    criterion_id: str
    question_id: str
    question_text: str
    description: str
    max_marks: float
    keywords: Optional[List[str]] = []


class RubricCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    total_marks: float
    criteria: List[CriterionIn]


class ReviewRequest(BaseModel):
    action: str
    override_score: Optional[float] = None


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Online", "project": "GradeOps", "version": "2.0.0"}


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/signup", status_code=201)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=data.password,
        role=data.role,
        dept_code=data.dept_code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created", "user_id": user.id, "role": user.role}


@app.post("/api/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.hashed_password != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "email": user.email,
    }


# ── Rubrics ──────────────────────────────────────────────────────────────────

@app.post("/api/rubrics", status_code=201)
def create_rubric(data: RubricCreateRequest, db: Session = Depends(get_db)):
    rubric = models.Rubric(
        name=data.name,
        description=data.description,
        total_marks=data.total_marks,
    )
    db.add(rubric)
    db.flush()
    for c in data.criteria:
        db.add(models.RubricCriterion(
            rubric_id=rubric.id,
            criterion_id=c.criterion_id,
            question_id=c.question_id,
            question_text=c.question_text,
            description=c.description,
            max_marks=c.max_marks,
            keywords=c.keywords,
        ))
    db.commit()
    db.refresh(rubric)
    return {"rubric_id": rubric.id, "name": rubric.name, "total_marks": rubric.total_marks}


@app.get("/api/rubrics")
def list_rubrics(db: Session = Depends(get_db)):
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "total_marks": r.total_marks,
            "criteria_count": len(r.criteria),
        }
        for r in db.query(models.Rubric).all()
    ]


# ── Script upload & grading ──────────────────────────────────────────────────

@app.post("/api/upload-script", status_code=201)
async def upload_script(
    background_tasks: BackgroundTasks,
    student_roll: str = Form(...),
    assignment_name: str = Form(""),
    rubric_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Clean rubric_id — empty string from form becomes None
    final_rubric_id = None
    if rubric_id and rubric_id.strip():
        try:
            final_rubric_id = int(rubric_id.strip())
        except ValueError:
            raise HTTPException(status_code=422, detail="rubric_id must be a number")

    safe_filename = f"{student_roll}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    with file_path.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)

    script = models.StudentScript(
        filename=safe_filename,
        file_path=str(file_path),
        student_roll=student_roll,
        assignment_name=assignment_name,
        rubric_id=final_rubric_id,
        status="pending",
    )
    db.add(script)
    db.commit()
    db.refresh(script)

    if final_rubric_id:
        background_tasks.add_task(run_grading_for_script, script.id)
        msg = f"Grading started in background for {student_roll}"
    else:
        msg = "Uploaded — attach a rubric and call /api/grade/{id}"

    return {
        "status": "success",
        "db_id": script.id,
        "filename": safe_filename,
        "message": msg,
        "file_url": f"/uploads/{safe_filename}",
    }


@app.post("/api/grade/{script_id}")
def trigger_grading(
    script_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    script = (
        db.query(models.StudentScript)
        .filter(models.StudentScript.id == script_id)
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if not script.rubric_id:
        raise HTTPException(status_code=400, detail="No rubric attached to this script")
    background_tasks.add_task(run_grading_for_script, script_id)
    return {"message": f"Grading triggered for script {script_id}"}


# ── Dashboard & detail ───────────────────────────────────────────────────────

@app.get("/api/dashboard")
def dashboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.StudentScript)
    if status:
        query = query.filter(models.StudentScript.status == status)
    total = query.count()
    scripts = (
        query.order_by(models.StudentScript.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for s in scripts:
        grading = s.grading_results
        ta = sum(g.final_score for g in grading)
        tp = sum(g.max_marks for g in grading)
        items.append({
            "id": s.id,
            "student_roll": s.student_roll,
            "assignment_name": s.assignment_name,
            "filename": s.filename,
            "file_url": f"/uploads/{s.filename}",
            "status": s.status,
            "total_awarded": ta,
            "total_possible": tp,
            "percentage": round(ta / tp * 100, 1) if tp else 0,
            "plagiarism_flagged": any(g.plagiarism_flag for g in grading),
            "uploaded_at": s.uploaded_at.isoformat() if s.uploaded_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@app.get("/api/scripts/{script_id}")
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = (
        db.query(models.StudentScript)
        .filter(models.StudentScript.id == script_id)
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {
        "id": script.id,
        "student_roll": script.student_roll,
        "assignment_name": script.assignment_name,
        "filename": script.filename,
        "file_url": f"/uploads/{script.filename}",
        "status": script.status,
        "rubric_id": script.rubric_id,
        "uploaded_at": script.uploaded_at.isoformat() if script.uploaded_at else None,
        "grading_results": [
            {
                "id": gr.id,
                "question_id": gr.question_id,
                "total_awarded": gr.total_awarded,
                "max_marks": gr.max_marks,
                "final_score": gr.final_score,
                "overall_justification": gr.overall_justification,
                "plagiarism_flag": gr.plagiarism_flag,
                "plagiarism_note": gr.plagiarism_note,
                "ta_approved": gr.ta_approved,
                "ta_flagged": gr.ta_flagged,
                "ta_override_score": gr.ta_override_score,
                "criteria_scores": [
                    {
                        "criterion_id": cs.criterion_id,
                        "awarded": cs.awarded,
                        "justification": cs.justification,
                        "met": cs.met,
                    }
                    for cs in gr.criterion_scores
                ],
            }
            for gr in script.grading_results
        ],
    }


# ── TA review ────────────────────────────────────────────────────────────────

@app.patch("/api/scripts/{script_id}/review")
def review_script(script_id: int, body: ReviewRequest, db: Session = Depends(get_db)):
    script = (
        db.query(models.StudentScript)
        .filter(models.StudentScript.id == script_id)
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if body.action == "approve":
        script.status = "approved"
        for gr in script.grading_results:
            gr.ta_approved = True
            gr.ta_flagged = False
    elif body.action == "flag":
        script.status = "flagged"
        for gr in script.grading_results:
            gr.ta_flagged = True
            gr.ta_approved = False
    elif body.action == "override":
        if body.override_score is None:
            raise HTTPException(status_code=400, detail="override_score required")
        for gr in script.grading_results:
            gr.ta_override_score = body.override_score
        script.status = "approved"
    else:
        raise HTTPException(status_code=400, detail="action must be: approve | flag | override")

    db.commit()
    return {"message": f"Script {script_id} marked as '{body.action}'"}


# ── Plagiarism flags ─────────────────────────────────────────────────────────

@app.get("/api/plagiarism-flags")
def plagiarism_flags(db: Session = Depends(get_db)):
    flagged = (
        db.query(models.GradingResult)
        .filter(models.GradingResult.plagiarism_flag == True)
        .all()
    )
    seen, results = set(), []
    for gr in flagged:
        key = (gr.question_id, gr.plagiarism_note or "")
        if key not in seen:
            seen.add(key)
            results.append({
                "script_id": gr.script_id,
                "student_roll": gr.script.student_roll,
                "question_id": gr.question_id,
                "plagiarism_note": gr.plagiarism_note,
            })
    return results


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)