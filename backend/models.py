

"""
GradeOps - SQLAlchemy Models
Tables: users, scripts, rubrics, rubric_criteria, grading_results, criterion_scores
"""
 
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
 
 
class User(Base):
    __tablename__ = "users"
 
    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(120), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20), nullable=False)   # 'TA' | 'Instructor'
    dept_code       = Column(String(20), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
 
    # Relationships
    scripts         = relationship("StudentScript", back_populates="uploader")
    rubrics         = relationship("Rubric", back_populates="created_by_user")
 
 
class StudentScript(Base):
    __tablename__ = "scripts"
 
    id              = Column(Integer, primary_key=True, index=True)
    filename        = Column(String(255), nullable=False)
    file_path       = Column(String(512), nullable=False)
    student_roll    = Column(String(50), nullable=False, index=True)
    assignment_name = Column(String(255), nullable=True)
    status          = Column(String(20), default="pending")  # pending | graded | approved | flagged
    uploaded_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    rubric_id       = Column(Integer, ForeignKey("rubrics.id"), nullable=True)
    uploaded_at     = Column(DateTime(timezone=True), server_default=func.now())
 
    # Relationships
    uploader        = relationship("User", back_populates="scripts")
    rubric          = relationship("Rubric", back_populates="scripts")
    grading_results = relationship("GradingResult", back_populates="script", cascade="all, delete-orphan")
 
 
class Rubric(Base):
    __tablename__ = "rubrics"
 
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    total_marks     = Column(Float, nullable=False)
    created_by      = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
 
    # Relationships
    created_by_user = relationship("User", back_populates="rubrics")
    criteria        = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan")
    scripts         = relationship("StudentScript", back_populates="rubric")
 
 
class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
 
    id              = Column(Integer, primary_key=True, index=True)
    rubric_id       = Column(Integer, ForeignKey("rubrics.id"), nullable=False)
    criterion_id    = Column(String(20), nullable=False)   # "C1", "C2" …
    question_id     = Column(String(20), nullable=False)   # "Q1", "Q2" …
    question_text   = Column(Text, nullable=False)
    description     = Column(Text, nullable=False)
    max_marks       = Column(Float, nullable=False)
    keywords        = Column(JSON, default=list)           # ["O(n log n)", ...]
 
    # Relationships
    rubric          = relationship("Rubric", back_populates="criteria")
 
 
class GradingResult(Base):
    __tablename__ = "grading_results"
 
    id                    = Column(Integer, primary_key=True, index=True)
    script_id             = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    question_id           = Column(String(20), nullable=False)
    total_awarded         = Column(Float, nullable=False, default=0.0)
    max_marks             = Column(Float, nullable=False, default=0.0)
    overall_justification = Column(Text, nullable=True)
    plagiarism_flag       = Column(Boolean, default=False)
    plagiarism_note       = Column(Text, nullable=True)
    ta_override_score     = Column(Float, nullable=True)   # TA can override AI score
    ta_approved           = Column(Boolean, default=False)
    ta_flagged            = Column(Boolean, default=False)
    graded_at             = Column(DateTime(timezone=True), server_default=func.now())
 
    # Relationships
    script                = relationship("StudentScript", back_populates="grading_results")
    criterion_scores      = relationship("CriterionScore", back_populates="grading_result", cascade="all, delete-orphan")
 
    @property
    def final_score(self) -> float:
        """Return TA override if set, else AI score."""
        return self.ta_override_score if self.ta_override_score is not None else self.total_awarded
 
 
class CriterionScore(Base):
    __tablename__ = "criterion_scores"
 
    id                = Column(Integer, primary_key=True, index=True)
    grading_result_id = Column(Integer, ForeignKey("grading_results.id"), nullable=False)
    criterion_id      = Column(String(20), nullable=False)
    awarded           = Column(Float, nullable=False, default=0.0)
    justification     = Column(Text, nullable=True)
    met               = Column(Boolean, default=False)
 
    # Relationships
    grading_result    = relationship("GradingResult", back_populates="criterion_scores")