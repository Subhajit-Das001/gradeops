# 📚 GRADEOPS — Smart AI Grading System

> Making exam evaluation faster, fairer, and a lot less painful.

---

## 🚀 About the Project

Grading handwritten exam papers is honestly exhausting. It takes a lot of time, consistency is hard to maintain, and small mistakes can easily happen—especially when checking hundreds of scripts.

**GRADEOPS** is our attempt to solve this problem using AI.

The idea is simple:

* Let AI do the heavy lifting (reading + grading)
* Keep humans in control for final decisions

So instead of replacing teachers, GRADEOPS **assists them**.

---

## 💡 What it does

* Upload exam papers (PDF/images)
* Extract handwritten answers using AI
* Grade answers based on a rubric
* Show marks with clear explanations
* Let TAs review and override if needed

---

## ✨ Key Features

### 📄 Easy Upload

Upload multiple answer sheets along with a structured rubric.

---

### 🔍 Handwriting to Text

Uses modern models to convert handwritten answers into readable text.

---

### 🤖 AI Grading

* Evaluates answers based on given rules
* Gives partial marks
* Explains *why* marks were given

---

### 👨‍🏫 Human Review (Important!)

* TAs can approve or change AI grades
* Keeps the system reliable and fair

---

### ⚡ Clean Dashboard

* View answer + grade side by side
* Quickly approve or edit scores

---

### 🔐 Role-Based Access

Different access for instructors and TAs.

---

## 🧠 How it works (simple view)

```id="q7azq3"
Upload Papers + Rubric
        ↓
Extract Text (OCR)
        ↓
AI Grades Answers
        ↓
Show Score + Explanation
        ↓
TA Reviews
        ↓
Final Marks Saved
```

---

## 🛠️ Tech Stack

We kept the stack practical and focused:

* **ML**: Python, PyTorch, Hugging Face
* **LLM Pipeline**: LangChain / LangGraph
* **Backend**: FastAPI
* **Frontend**: React.js
* **Database**: PostgreSQL / MongoDB

---

## 📁 Project Structure

```id="yt2p36"
gradeops/
├── backend/
├── frontend/
├── ml/
├── database/
├── data/
└── docs/
```

---

## ⚙️ How to Run

### 1. Clone the repo

```id="c8z9l1"
git clone https://github.com/Subhajit-Das001/gradeops.git
cd gradeops
```

### 2. Start backend

```id="0q6vsi"
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Start frontend

```id="mf5l7y"
cd frontend
npm install
npm run dev
```

---

## 🎯 Why we built this

We wanted to work on something:

* Practical
* Useful in real academic settings
* Combines ML + Web development

GRADEOPS is our way of exploring how AI can actually help in education instead of just being a buzzword.

---

## 🚧 What’s next

* Plagiarism detection
* Better handwriting recognition
* Performance analytics dashboard
* Cloud deployment

---

## 👥 Team

* Subhajit Das

---

## 📌 Final Note

This project is not about replacing teachers.
It’s about **helping them save time and make better decisions**.

---

## ⭐ If you like it

Give it a star ⭐ or feel free to contribute!
