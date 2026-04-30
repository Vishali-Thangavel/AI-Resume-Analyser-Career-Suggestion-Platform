# ResumAI – AI Resume Analyzer

A full-stack AI-powered resume analyzer and career suggestion web application.

---

## 🚀 Features

- **Resume Upload**: PDF, DOCX, TXT support
- **ATS Compatibility Check**: Score your resume against ATS systems
- **Skill Extraction**: Auto-detect skills from your resume
- **Skill Gap Analysis**: Compare your skills vs job description requirements
- **Resume Score (0–100)**: Composite score across ATS, skills, and structure
- **Detailed Report**: Positives, weaknesses, missing skills, and AI suggestions
- **Resume Builder**: Generate ATS-optimized resume text
- **Auth System**: Register/Login with Free vs Premium handling
- **SQLite Database**: Stores users, resumes, and analysis history
- **Optional OpenAI**: Set `OPENAI_API_KEY` for GPT-powered suggestions

---

## 📁 Project Structure

```
resume_analyzer/
├── backend/
│   ├── app.py          # Flask routes & API
│   ├── ai_engine.py    # NLP analysis engine
│   ├── file_parser.py  # PDF/DOCX/TXT parser
│   └── database.db     # Auto-created SQLite DB
├── frontend/
│   ├── templates/
│   │   ├── index.html
│   │   ├── analyzer.html
│   │   ├── result.html
│   │   ├── builder.html
│   │   ├── login.html
│   │   └── register.html
│   └── static/
│       ├── css/main.css
│       └── js/main.js
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone / Extract the project

```bash
cd resume_analyzer
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Add OpenAI API key for AI-powered suggestions

```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here

# macOS/Linux
export OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the app

```bash
cd backend
python app.py
```

### 6. Open in browser

```
http://localhost:5000
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/me` | Get current user |
| POST | `/api/analyze` | Analyze resume (multipart or JSON) |
| GET | `/api/history` | Get analysis history (auth required) |

---

## 📊 Scoring System

| Component | Weight |
|-----------|--------|
| ATS Score | 35% |
| Skill Match | 45% |
| Sections Present | 10% |
| Contact Info | 10% |

---

## 💡 Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-CORS
- **Frontend**: HTML5, CSS3 (custom design system), Vanilla JS
- **Database**: SQLite via Python's built-in `sqlite3`
- **AI/NLP**: Regex + keyword taxonomy (no heavy ML deps)
- **File Parsing**: pdfplumber, PyPDF2, python-docx
- **Optional AI**: OpenAI GPT-3.5 for enriched suggestions

---

## 📝 License

MIT License — free for personal and educational use.
