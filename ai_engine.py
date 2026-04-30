"""
ai_engine.py – Core NLP/AI logic for resume analysis.
Uses regex + keyword matching (no external NLP deps required).
Drop in an OPENAI_API_KEY env-var to get GPT-powered suggestions.
"""

import re
import os
import json
from collections import defaultdict

# ─── SKILL TAXONOMY ───────────────────────────────────────────────────────────

SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "perl",
    ],
    "Web Frameworks": [
        "react", "angular", "vue", "django", "flask", "fastapi", "express",
        "spring", "laravel", "rails", "next.js", "nuxt", "svelte",
    ],
    "Data & AI": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        "sql", "nosql", "spark", "hadoop", "tableau", "power bi",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "github actions", "ci/cd", "linux", "bash",
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "sqlite", "oracle", "dynamodb", "cassandra",
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "project management", "agile", "scrum", "critical thinking",
        "time management", "collaboration",
    ],
}

ATS_KEYWORDS = [
    "quantified", "achieved", "improved", "reduced", "increased", "led",
    "managed", "developed", "implemented", "designed", "built", "created",
    "optimized", "delivered", "launched", "coordinated", "automated",
]

SECTION_HEADERS = {
    "education": ["education", "qualification", "degree", "academic"],
    "experience": ["experience", "work history", "employment", "career"],
    "skills": ["skills", "technologies", "technical skills", "competencies"],
    "projects": ["projects", "portfolio", "work samples"],
    "certifications": ["certification", "certificate", "award", "achievement"],
    "summary": ["summary", "objective", "profile", "about"],
}

JOB_ROLE_SKILLS = {
    "software engineer": ["python", "java", "algorithms", "data structures", "git", "sql"],
    "data scientist": ["python", "machine learning", "statistics", "pandas", "sql", "tensorflow"],
    "frontend developer": ["javascript", "react", "css", "html", "typescript", "vue"],
    "backend developer": ["python", "java", "sql", "rest api", "docker", "node.js"],
    "devops engineer": ["docker", "kubernetes", "aws", "ci/cd", "linux", "terraform"],
    "ml engineer": ["python", "tensorflow", "pytorch", "mlops", "docker", "spark"],
    "product manager": ["agile", "scrum", "roadmap", "stakeholder", "kpi", "communication"],
    "data analyst": ["sql", "excel", "tableau", "python", "statistics", "power bi"],
    "full stack developer": ["javascript", "react", "node.js", "sql", "rest api", "docker"],
    "cybersecurity": ["penetration testing", "firewall", "siem", "encryption", "linux"],
}

# ─── MAIN ANALYZER ────────────────────────────────────────────────────────────

class ResumeAnalyzer:

    def analyze(self, resume_text: str, job_role: str = "", job_description: str = "") -> dict:
        text_lower = resume_text.lower()

        skills_found = self._extract_skills(text_lower)
        sections = self._detect_sections(text_lower)
        ats_score, ats_issues = self._ats_check(resume_text, text_lower, sections)
        jd_skills = self._extract_jd_skills(job_description, job_role)
        match_score, missing_skills = self._match_score(skills_found, jd_skills)
        word_count = len(resume_text.split())
        contact_ok = self._has_contact(text_lower)

        score = self._compute_score(ats_score, match_score, sections, word_count, contact_ok)

        positives = self._positives(skills_found, sections, ats_score, contact_ok, word_count)
        weaknesses = self._weaknesses(ats_issues, missing_skills, sections, word_count, contact_ok)
        suggestions = self._suggestions(weaknesses, job_role, skills_found)

        # Optional OpenAI enrichment
        ai_tip = self._openai_tip(resume_text, job_role, job_description)

        return {
            "score": score,
            "ats_score": ats_score,
            "match_score": match_score,
            "skills_found": skills_found,
            "missing_skills": missing_skills[:10],
            "sections_detected": sections,
            "positives": positives,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "ai_tip": ai_tip,
            "word_count": word_count,
            "job_role": job_role,
        }

    # ── SKILL EXTRACTION ──────────────────────────────────────────────────────

    def _extract_skills(self, text: str) -> dict:
        found = defaultdict(list)
        for category, skills in SKILL_TAXONOMY.items():
            for skill in skills:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text):
                    found[category].append(skill)
        return dict(found)

    def _extract_jd_skills(self, jd: str, role: str) -> list:
        skills = set()
        jd_lower = jd.lower()
        for category, skill_list in SKILL_TAXONOMY.items():
            for skill in skill_list:
                if re.search(r'\b' + re.escape(skill) + r'\b', jd_lower):
                    skills.add(skill)
        # Add role-based expected skills
        for key, role_skills in JOB_ROLE_SKILLS.items():
            if key in role.lower():
                skills.update(role_skills)
        return list(skills)

    # ── SECTION DETECTION ─────────────────────────────────────────────────────

    def _detect_sections(self, text: str) -> list:
        found = []
        for section, keywords in SECTION_HEADERS.items():
            for kw in keywords:
                if kw in text:
                    found.append(section)
                    break
        return found

    # ── ATS CHECK ─────────────────────────────────────────────────────────────

    def _ats_check(self, original: str, text_lower: str, sections: list) -> tuple:
        score = 100
        issues = []

        # Action verbs
        verb_count = sum(1 for v in ATS_KEYWORDS if v in text_lower)
        if verb_count < 3:
            score -= 20
            issues.append("Few or no strong action verbs (achieved, led, built…)")

        # Sections
        for s in ["experience", "education", "skills"]:
            if s not in sections:
                score -= 10
                issues.append(f"Missing '{s}' section header")

        # No tables / columns (heuristic: excessive tabs)
        if original.count('\t') > 20:
            score -= 10
            issues.append("Possible table layout — ATS may mis-parse columns")

        # Contact info
        if not self._has_contact(text_lower):
            score -= 10
            issues.append("Missing contact information (email/phone)")

        # Length
        wc = len(original.split())
        if wc < 200:
            score -= 15
            issues.append("Resume too short (< 200 words)")
        elif wc > 1200:
            score -= 5
            issues.append("Resume may be too long (> 1200 words)")

        # Special characters
        if len(re.findall(r'[★●■◆▶►]', original)) > 5:
            score -= 5
            issues.append("Special bullet characters may confuse ATS parsers")

        return max(0, score), issues

    # ── CONTACT ───────────────────────────────────────────────────────────────

    def _has_contact(self, text: str) -> bool:
        email = bool(re.search(r'[\w.-]+@[\w.-]+\.\w+', text))
        phone = bool(re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text))
        return email or phone

    # ── MATCH SCORE ───────────────────────────────────────────────────────────

    def _match_score(self, skills_found: dict, jd_skills: list) -> tuple:
        if not jd_skills:
            return 70, []
        all_found = {s for skills in skills_found.values() for s in skills}
        matched = [s for s in jd_skills if s in all_found]
        missing = [s for s in jd_skills if s not in all_found]
        pct = int(len(matched) / len(jd_skills) * 100) if jd_skills else 70
        return pct, missing

    # ── COMPOSITE SCORE ───────────────────────────────────────────────────────

    def _compute_score(self, ats, match, sections, wc, contact):
        score = int(ats * 0.35 + match * 0.45 + (len(sections) / 6) * 100 * 0.1 + (10 if contact else 0))
        return max(1, min(100, score))

    # ── POSITIVES ─────────────────────────────────────────────────────────────

    def _positives(self, skills, sections, ats_score, contact, wc):
        pos = []
        total_skills = sum(len(v) for v in skills.values())
        if total_skills > 5:
            pos.append(f"Strong skill set detected: {total_skills} relevant skills found across {len(skills)} categories")
        if "experience" in sections:
            pos.append("Work experience section clearly present — good for ATS parsing")
        if "education" in sections:
            pos.append("Education section detected and well-structured")
        if contact:
            pos.append("Contact information found — recruiter can reach you easily")
        if ats_score >= 70:
            pos.append(f"ATS compatibility score is solid ({ats_score}/100)")
        if 300 <= wc <= 900:
            pos.append(f"Resume length ({wc} words) is within the ideal range")
        if "projects" in sections:
            pos.append("Projects section found — great for showcasing practical work")
        if "certifications" in sections:
            pos.append("Certifications listed — adds credibility to your profile")
        if not pos:
            pos.append("Resume text successfully extracted and parsed")
        return pos

    # ── WEAKNESSES ────────────────────────────────────────────────────────────

    def _weaknesses(self, ats_issues, missing, sections, wc, contact):
        weak = list(ats_issues)
        if missing:
            weak.append(f"Missing {len(missing)} skills expected for this role: {', '.join(missing[:5])}" + ("…" if len(missing) > 5 else ""))
        if "summary" not in sections:
            weak.append("No professional summary/objective — add a 2–3 line pitch at the top")
        if wc < 200:
            weak.append("Resume content is very thin — expand with more details")
        return weak

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────

    def _suggestions(self, weaknesses, job_role, skills):
        tips = []
        if "Missing" in str(weaknesses):
            tips.append("Add missing skills to a dedicated Skills section (even beginner-level ones)")
        tips.append("Quantify achievements: replace 'worked on' with 'reduced X by 30%'")
        tips.append("Use a clean single-column ATS-friendly template (no tables, no graphics)")
        if job_role:
            tips.append(f"Tailor the summary and skills sections specifically for '{job_role}' roles")
        tips.append("Include a LinkedIn URL and GitHub profile in contact info")
        tips.append("Keep your resume to 1 page (< 3 years exp) or 2 pages max")
        tips.append("Start every bullet with a strong past-tense action verb")
        return tips

    # ── OPENAI TIP (optional) ─────────────────────────────────────────────────

    def _openai_tip(self, resume: str, role: str, jd: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ""
        try:
            import openai
            openai.api_key = api_key
            prompt = (
                f"You are a professional career coach. Analyze this resume for the role '{role}' "
                f"and give 3 concise, actionable improvement tips (max 80 words total).\n\n"
                f"RESUME (first 800 chars):\n{resume[:800]}\n\n"
                f"JD SNIPPET:\n{jd[:400]}"
            )
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return ""
