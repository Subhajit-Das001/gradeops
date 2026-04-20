"""
GradeOps - Agentic LLM Grading Pipeline
Uses LangChain / LangGraph to:
  1. Grade each answer against a rubric with partial credit
  2. Generate structured justifications
  3. Flag potential plagiarism across submissions
"""
 
import os
import json
from typing import TypedDict, Annotated, Sequence
from dataclasses import dataclass, field, asdict
 
       # swap for any ChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from typing import Optional
import operator
import torch
 
 
# ── Data models ───────────────────────────────────────────────────────────────
@dataclass
class RubricCriterion:
    criterion_id: str       # e.g. "C1"
    description: str        # e.g. "Defines time complexity correctly"
    max_marks: float
    keywords: list[str] = field(default_factory=list)  # optional hints
 
 
@dataclass
class QuestionRubric:
    question_id: str        # e.g. "Q1"
    question_text: str
    total_marks: float
    criteria: list[RubricCriterion]
 
 
class CriterionScore(BaseModel):
    criterion_id: str
    awarded: float   = Field(description="Marks awarded for this criterion")
    justification: str = Field(description="1-2 sentence explanation")
    met: bool        = Field(description="Whether the criterion was fully met")
 
 
class GradingResult(BaseModel):
    question_id: str
    total_awarded: float
    max_marks: float
    criteria_scores: list[CriterionScore]
    overall_justification: str
    plagiarism_flag: bool = False
    plagiarism_note: str  = ""
 
 
# ── LangGraph state ───────────────────────────────────────────────────────────
from typing import Optional
class GradingState(TypedDict):
    question_id:    str
    question_text:  str
    student_answer: str
    rubric:         dict
    grading_result: Optional[GradingResult]
    messages:       Annotated[list, operator.add]
# ── LLM setup ─────────────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

def build_llm():
    llm = HuggingFacePipeline.from_model_id(
        model_id=LLM_MODEL,
        task="text-generation",
        device_map="auto",
        model_kwargs={
            "torch_dtype": torch.float16,
            "token": os.getenv("HF_TOKEN"),
        },
        pipeline_kwargs={
            "max_new_tokens": 1024,
            "temperature": 0.1,
            "do_sample": True,
        },
    )
    return ChatHuggingFace(llm=llm)
# ── Grading prompts ───────────────────────────────────────────────────────────
SYSTEM_GRADING = """You are a strict but fair university exam grader.
You will be given:
- A student's handwritten answer (transcribed)
- A grading rubric with individual criteria and mark allocations
 
Your job:
1. Evaluate each criterion independently.
2. Award partial marks where partial understanding is demonstrated.
3. Provide a 1-2 sentence justification per criterion.
4. Sum up awarded marks. Never exceed the max marks per criterion.
5. Return ONLY valid JSON matching the schema below.
 
Schema:
{
  "question_id": "...",
  "total_awarded": <float>,
  "max_marks": <float>,
  "criteria_scores": [
    {
      "criterion_id": "...",
      "awarded": <float>,
      "justification": "...",
      "met": <bool>
    }
  ],
  "overall_justification": "..."
}
"""
 
def build_grading_prompt(state: GradingState) -> list:
    rubric = state["rubric"]
    criteria_text = "\n".join(
        f"  [{c['criterion_id']}] ({c['max_marks']} marks) {c['description']}"
        + (f" | Keywords: {', '.join(c['keywords'])}" if c.get("keywords") else "")
        for c in rubric["criteria"]
    )
    human = (
        f"Question ({state['question_id']}): {state['question_text']}\n\n"
        f"Rubric Criteria:\n{criteria_text}\n"
        f"Total marks available: {rubric['total_marks']}\n\n"
        f"Student Answer:\n---\n{state['student_answer']}\n---\n\n"
        "Grade this answer."
    )
    return [SystemMessage(content=SYSTEM_GRADING), HumanMessage(content=human)]
 
 
# ── Graph nodes ───────────────────────────────────────────────────────────────
def grade_answer(state: GradingState) -> GradingState:
    """Node: call LLM to grade the answer."""
    llm = build_llm()
    messages = build_grading_prompt(state)
    response = llm.invoke(messages)
    raw = json.loads(response.content)
 
    result = GradingResult(
        question_id=raw["question_id"],
        total_awarded=raw["total_awarded"],
        max_marks=raw["max_marks"],
        criteria_scores=[CriterionScore(**cs) for cs in raw["criteria_scores"]],
        overall_justification=raw.get("overall_justification", ""),
    )
    return {**state, "grading_result": result, "messages": [response]}
 
 
def validate_marks(state: GradingState) -> GradingState:
    """Node: clamp awarded marks so they never exceed rubric maxima."""
    result = state["grading_result"]
    rubric_map = {c["criterion_id"]: c["max_marks"] for c in state["rubric"]["criteria"]}
 
    fixed_scores = []
    for cs in result.criteria_scores:
        max_m = rubric_map.get(cs.criterion_id, cs.awarded)
        clamped = min(cs.awarded, max_m)
        fixed_scores.append(CriterionScore(
            criterion_id=cs.criterion_id,
            awarded=clamped,
            justification=cs.justification,
            met=cs.met,
        ))
 
    total = sum(cs.awarded for cs in fixed_scores)
    result.criteria_scores = fixed_scores
    result.total_awarded = total
    return {**state, "grading_result": result}
 
 
def should_regrade(state: GradingState) -> str:
    """Edge: if total awarded doesn't match sum of criteria, regrade once."""
    result = state["grading_result"]
    computed = sum(cs.awarded for cs in result.criteria_scores)
    if abs(computed - result.total_awarded) > 0.01:
        return "grade_answer"   # loop back
    return "done"
 
 
# ── LangGraph pipeline ────────────────────────────────────────────────────────
def build_grading_graph():
    graph = StateGraph(GradingState)
    graph.add_node("grade_answer", grade_answer)
    graph.add_node("validate_marks", validate_marks)
 
    graph.set_entry_point("grade_answer")
    graph.add_edge("grade_answer", "validate_marks")
    graph.add_conditional_edges(
        "validate_marks",
        should_regrade,
        {"grade_answer": "grade_answer", "done": END},
    )
    return graph.compile()
 
 
# ── Public grading API ────────────────────────────────────────────────────────
def grade_single_answer(
    question_rubric: QuestionRubric,
    student_answer: str,
) -> GradingResult:
    """Grade one student answer against the given rubric."""
    graph = build_grading_graph()
    state: GradingState = {
        "question_id":    question_rubric.question_id,
        "question_text":  question_rubric.question_text,
        "student_answer": student_answer,
        "rubric":         asdict(question_rubric),
        "grading_result": None,
        "messages":       [],
    }
    final = graph.invoke(state)
    return final["grading_result"]
 
 
def grade_exam(
    rubric_map: dict[str, QuestionRubric],
    answers: list[dict],
) -> list[GradingResult]:
    """
    Grade all answers from one exam.
 
    Parameters
    ----------
    rubric_map : dict mapping question_id → QuestionRubric
    answers    : list of {"question_id": ..., "raw_text": ...}
    """
    results = []
    for ans in answers:
        qid = ans["question_id"]
        rubric = rubric_map.get(qid)
        if rubric is None:
            continue
        result = grade_single_answer(rubric, ans["raw_text"])
        results.append(result)
    return results
 
 
# ── Plagiarism detection ──────────────────────────────────────────────────────
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
 
 
def detect_plagiarism(
    submissions: list[dict],   # [{"student_id": ..., "question_id": ..., "raw_text": ...}]
    threshold: float = 0.85,
) -> list[dict]:
    """
    Vectorize all answers per question and flag pairs with cosine similarity
    above `threshold`.
 
    Returns list of flagged pairs:
    [{"question_id", "student_a", "student_b", "similarity"}]
    """
    from collections import defaultdict
    by_question: dict[str, list] = defaultdict(list)
    for sub in submissions:
        by_question[sub["question_id"]].append(sub)
 
    flags = []
    for qid, subs in by_question.items():
        if len(subs) < 2:
            continue
        texts = [s["raw_text"] for s in subs]
        ids   = [s["student_id"] for s in subs]
 
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
        tfidf = vec.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf)
 
        n = len(subs)
        for i in range(n):
            for j in range(i + 1, n):
                sim = sim_matrix[i, j]
                if sim >= threshold:
                    flags.append({
                        "question_id": qid,
                        "student_a": ids[i],
                        "student_b": ids[j],
                        "similarity": round(float(sim), 4),
                    })
 
    return sorted(flags, key=lambda x: -x["similarity"])
 
 
# ── Attach plagiarism notes to grading results ────────────────────────────────
def annotate_plagiarism(
    grading_results: dict[str, list[GradingResult]],  # student_id → results
    plagiarism_flags: list[dict],
) -> None:
    """Mutate GradingResult objects in-place to set plagiarism fields."""
    flagged_set = set()
    for flag in plagiarism_flags:
        flagged_set.add((flag["student_a"], flag["question_id"]))
        flagged_set.add((flag["student_b"], flag["question_id"]))
        flag_msg = (
            f"High similarity ({flag['similarity']:.0%}) detected with "
            f"student {flag['student_b'] if flag['student_a'] in flagged_set else flag['student_a']}."
        )
        for sid, results in grading_results.items():
            for r in results:
                if (sid, r.question_id) in flagged_set:
                    r.plagiarism_flag = True
                    r.plagiarism_note = flag_msg
 
 
# ── Demo / smoke test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    rubric = QuestionRubric(
        question_id="Q1",
        question_text="Explain the time and space complexity of merge sort.",
        total_marks=10,
        criteria=[
            RubricCriterion("C1", "Correctly states O(n log n) time complexity", 4, ["O(n log n)"]),
            RubricCriterion("C2", "Correctly states O(n) auxiliary space", 3, ["O(n)"]),
            RubricCriterion("C3", "Briefly explains the divide-and-conquer reasoning", 3, ["divide", "merge", "recursion"]),
        ],
    )
 
    answer = (
        "Merge sort has a time complexity of O(n log n) because at each level of recursion "
        "we do O(n) work and there are log n levels. The space complexity is O(n) due to the "
        "temporary arrays needed during the merge step."
    )
 
    result = grade_single_answer(rubric, answer)
    print(json.dumps(asdict(result) if hasattr(result, "__dict__") else result.dict(), indent=2))