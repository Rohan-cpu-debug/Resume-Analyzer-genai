import PyPDF2
import re


class ResumeAnalyzerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.resume_text = ""
        self.skills = []

    # ---------- PDF TEXT EXTRACTION ----------
    def extract_text(self, file):
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # ---------- ATS COMPATIBILITY ----------
    def calculate_ats_score(self, role_requirements):
        text = self.resume_text.lower()

        total_keywords = max(len(role_requirements), 1)
        matched_keywords = sum(
            1 for skill in role_requirements if skill.lower() in text
        )

        keyword_score = (matched_keywords / total_keywords) * 70

        length_score = 30
        if len(self.resume_text) < 800:
            length_score = 15
        elif len(self.resume_text) > 5000:
            length_score = 20

        ats_score = min(int(keyword_score + length_score), 100)

        feedback = []
        if matched_keywords < total_keywords * 0.5:
            feedback.append("Low keyword match for the selected role.")
        if len(self.resume_text) < 800:
            feedback.append("Resume is too short for ATS systems.")
        if not feedback:
            feedback.append("Resume is ATS friendly.")

        return {
            "ats_score": ats_score,
            "matched_keywords": matched_keywords,
            "total_keywords": total_keywords,
            "ats_feedback": feedback
        }

    # ---------- RESUME ANALYSIS ----------
    def analyze_resume(self, resume_file, role_requirements, custom_jd=None):
        self.resume_text = self.extract_text(resume_file)
        self.skills = role_requirements

        resume_lower = self.resume_text.lower()
        total_skills = max(len(role_requirements), 1)

        matched = []
        missing = []

        for skill in role_requirements:
            if skill.lower() in resume_lower:
                matched.append(skill)
            else:
                missing.append(skill)

        skill_match_score = int((len(matched) / total_skills) * 40)

        critical_skills = role_requirements[:5]
        critical_total = max(len(critical_skills), 1)
        critical_matched = sum(
            1 for s in critical_skills if s.lower() in resume_lower
        )
        critical_score = int((critical_matched / critical_total) * 30)

        experience_keywords = ["experience", "intern", "worked", "company", "role"]
        experience_hits = sum(
            1 for k in experience_keywords if k in resume_lower
        )
        experience_score = min(experience_hits * 5, 20)

        structure_sections = ["skills", "experience", "education", "project"]
        structure_hits = sum(
            1 for s in structure_sections if s in resume_lower
        )
        structure_score = min(structure_hits * 2, 10)

        overall_score = min(
            skill_match_score + critical_score + experience_score + structure_score,
            100
        )

        ats = self.calculate_ats_score(role_requirements)

        return {
            "overall_score": overall_score,
            "strengths": matched,
            "missing_skills": missing,
            "selected": overall_score >= 70,
            "score_breakdown": {
                "skill_match": skill_match_score,
                "critical_skills": critical_score,
                "experience_relevance": experience_score,
                "resume_structure": structure_score
            },
            "ats_score": ats["ats_score"],
            "ats_keywords_matched": ats["matched_keywords"],
            "ats_total_keywords": ats["total_keywords"],
            "ats_feedback": ats["ats_feedback"]
        }

    # ---------- HELPERS ----------
    def _extract_projects(self):
        lines = self.resume_text.split("\n")
        return [
            l for l in lines
            if len(l.strip()) > 20 and
            any(k in l.lower() for k in ["system", "application", "project", "app", "model"])
        ][:5]

    def _extract_certifications(self):
        lines = self.resume_text.split("\n")
        return [
            l for l in lines
            if any(k in l.lower() for k in [
                "certified", "certification", "certificate",
                "coursera", "udemy", "aws", "google"
            ])
        ][:5]

    # ---------- RESUME Q&A ----------
    def ask_question(self, question):
        if not self.resume_text:
            return "Please analyze the resume first."

        q = question.lower()
        text = self.resume_text.lower()

        if "summary" in q:
            return "This resume shows relevant skills, projects, and experience aligned with the role."

        if "strength" in q:
            strengths = [s for s in self.skills if s.lower() in text][:6]
            return "Key Strengths:\n- " + "\n- ".join(strengths) if strengths else "Strengths not clear."

        if "project" in q:
            projects = self._extract_projects()
            return "Projects:\n- " + "\n- ".join(projects) if projects else "No projects identified."

        if "certification" in q:
            certs = self._extract_certifications()
            return "Certifications:\n- " + "\n- ".join(certs) if certs else "No certifications found."

        return "Answer based on resume:\n" + self.resume_text[:600]

    # ---------- INTERVIEW QUESTIONS ----------
    def generate_interview_questions(self, role, difficulty="Medium", count=10):
        if not self.resume_text:
            return ["Please analyze the resume first."]

        resume_lower = self.resume_text.lower()
        skills = [s for s in self.skills if s.lower() in resume_lower] or [role]

        if difficulty == "Easy":
            templates = [
                "What is {skill}?",
                "Why is {skill} important?",
                "Explain {skill} in simple terms.",
                "Where is {skill} used?",
                "What problem does {skill} solve?"
            ]
        elif difficulty == "Medium":
            templates = [
                "How have you used {skill} in a project?",
                "Explain a challenge using {skill}.",
                "Compare {skill} with an alternative.",
                "How do you debug issues in {skill}?",
                "What best practices do you follow for {skill}?"
            ]
        else:
            templates = [
                "Design a system using {skill}.",
                "What trade-offs exist with {skill}?",
                "How would you scale a {skill}-based system?",
                "How do you secure systems using {skill}?",
                "Explain internals of {skill}."
            ]

        questions = []
        i = 0
        while len(questions) < count:
            skill = skills[i % len(skills)]
            template = templates[i % len(templates)]
            questions.append(f"[{difficulty}] " + template.format(skill=skill))
            i += 1

        return questions

    # ---------- TECHNICAL ANSWER EVALUATION ----------
    def evaluate_interview_answer(self, question, answer, role, difficulty):
        if not answer.strip():
            return {
                "score": 0,
                "strengths": ["No answer provided"],
                "missing": ["Answer the question"],
                "improved_answer": "Please provide a complete answer."
            }

        keyword_hits = sum(1 for s in self.skills if s.lower() in answer.lower())
        score = min(10, max(3, keyword_hits + len(answer.split()) // 30))

        strengths = []
        if keyword_hits:
            strengths.append("Mentions relevant technical concepts")
        if len(answer.split()) > 40:
            strengths.append("Good explanation depth")

        missing = []
        if keyword_hits == 0:
            missing.append("No role-specific skills mentioned")
        if len(answer.split()) < 30:
            missing.append("Answer lacks depth")

        return {
            "score": score,
            "strengths": strengths or ["Basic attempt"],
            "missing": missing or ["Minor improvements needed"],
            "improved_answer": "Use examples, explain impact, and link to the role."
        }

    # ---------- HR ANSWER EVALUATION ----------
    def evaluate_hr_answer(self, question, answer):
        if not answer.strip():
            return {
                "score": 0,
                "strengths": ["No answer provided"],
                "improvements": ["Answer clearly and confidently"],
                "sample_answer": "Prepare a structured response with examples."
            }

        word_count = len(answer.split())
        score = min(10, max(4, word_count // 20))

        strengths = []
        if word_count > 40:
            strengths.append("Clear and detailed response")
        if "i" in answer.lower():
            strengths.append("Personal and confident tone")

        improvements = []
        if word_count < 30:
            improvements.append("Add more detail and examples")
        if "team" not in answer.lower():
            improvements.append("Mention teamwork or collaboration")

        return {
            "score": score,
            "strengths": strengths or ["Good basic response"],
            "improvements": improvements or ["Minor polishing needed"],
            "sample_answer": (
                "A strong HR answer is structured, honest, and includes a real-life example "
                "showing your skills, attitude, and growth."
            )
        }

    # ---------- RESUME IMPROVEMENT (NEW FEATURE – SAFE ADDITION) ----------
    def suggest_resume_improvements(self, role):
        suggestions = []

        if len(self.resume_text) < 800:
            suggestions.append("Increase resume length with more detailed project and experience descriptions.")

        missing_skills = [s for s in self.skills if s.lower() not in self.resume_text.lower()]
        if missing_skills:
            suggestions.append(
                "Consider adding or highlighting these skills: " + ", ".join(missing_skills[:5])
            )

        if not self._extract_projects():
            suggestions.append("Add a Projects section with measurable outcomes.")

        if not self._extract_certifications():
            suggestions.append("Include certifications or relevant courses to strengthen credibility.")

        suggestions.append("Use action verbs and quantify achievements (e.g., improved performance by 20%).")
        suggestions.append("Ensure the resume is tailored specifically for the " + role + " role.")

        return suggestions

    # ---------- DOWNLOADABLE REPORT ----------
    def generate_resume_report(self, analysis_result, role):
        breakdown = analysis_result.get("score_breakdown", {})

        return f"""
RESUME ANALYSIS REPORT
=====================

Target Role: {role}

Overall Score: {analysis_result['overall_score']} / 100
ATS Score: {analysis_result['ats_score']} / 100

Section Breakdown:
- Skill Match: {breakdown.get('skill_match', 0)} / 40
- Critical Skills: {breakdown.get('critical_skills', 0)} / 30
- Experience Relevance: {breakdown.get('experience_relevance', 0)} / 20
- Resume Structure: {breakdown.get('resume_structure', 0)} / 10

Missing Skills:
{", ".join(analysis_result.get("missing_skills", [])) or "None"}

Generated by Euron Recruitment Agent
""".strip()
