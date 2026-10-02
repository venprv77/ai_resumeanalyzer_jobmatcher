import os
import json
import re
import time

from google import genai
from google.genai import types
from config import Config


# ============================================================
# GEMINI API KEY
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY") or Config.GEMINI_API_KEY
if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY_HERE":

    raise ValueError(
        "GEMINI_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MODEL_FALLBACKS = [
    MODEL_NAME,
    "gemini-3.6-pro"
]
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
RETRY_ERROR_KEYWORDS = [
    "503",
    "UNAVAILABLE",
    "HIGH DEMAND",
    "TEMPORARY"
]


def is_retry_error(exception_text):
    if not exception_text:
        return False

    exception_text = exception_text.upper()
    return any(
        keyword in exception_text
        for keyword in RETRY_ERROR_KEYWORDS
    )


def fallback_analyze_resume(resume_text, job_description):
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    candidate_skills = [
        "python",
        "flask",
        "django",
        "restful apis",
        "postgresql",
        "mysql",
        "mongodb",
        "docker",
        "aws",
        "azure",
        "gcp",
        "git",
        "github",
        "sql",
        "javascript",
        "react",
        "node.js",
        "machine learning",
        "data structures",
        "algorithms",
        "oop",
        "api",
        "backend",
        "frontend"
    ]

    requested_skills = [
        skill for skill in candidate_skills
        if skill in job_lower
    ]

    if not requested_skills:
        requested_skills = []
        for line in job_description.splitlines():
            for token in re.findall(r"[A-Za-z0-9+\-#\.]{2,}", line):
                cleaned = token.strip(".,;()[]")
                if cleaned and len(cleaned) > 2:
                    requested_skills.append(cleaned)
        requested_skills = list(dict.fromkeys(requested_skills))[:10]

    matching_skills = [
        skill for skill in requested_skills
        if skill.lower() in resume_lower
    ]
    missing_skills = [
        skill for skill in requested_skills
        if skill.lower() not in resume_lower
    ]

    strengths = []
    if "python" in resume_lower:
        strengths.append("Strong Python programming experience")
    if re.search(r"\b(mysql|postgresql|mongodb|database|dbms)\b", resume_lower):
        strengths.append("Database development and integration experience")
    if re.search(r"\b(machine learning|data science|ml)\b", resume_lower):
        strengths.append("Experience with machine learning or data-driven projects")
    if re.search(r"\b(git|github)\b", resume_lower):
        strengths.append("Version control experience with Git/GitHub")
    if not strengths:
        strengths.append("Solid technical foundation with project-based experience")

    weaknesses = []
    if "django" not in resume_lower and "flask" not in resume_lower:
        weaknesses.append("Limited evidence of Python web framework experience")
    if "docker" not in resume_lower and "kubernetes" not in resume_lower:
        weaknesses.append("No clear containerization or cloud deployment experience")
    if "rest" not in resume_lower and "api" not in resume_lower:
        weaknesses.append("No explicit REST API development experience")
    if not weaknesses:
        weaknesses.append("Resume could be more detailed on specific project achievements")

    suggestions = []
    if missing_skills:
        suggestions.append(
            "Add or emphasize the missing job-specific skills from the job description."
        )
    else:
        suggestions.append(
            "Highlight your achievements and measurable outcomes in current projects."
        )
    suggestions.append(
        "Include any backend, API, or cloud technologies if applicable to the role."
    )
    suggestions.append(
        "Describe project impact, tools used, and results for stronger alignment with the job."
    )

    recommended_roles = []
    if "python" in resume_lower:
        recommended_roles.append("Junior Python Developer")
    if "machine learning" in resume_lower or "data science" in resume_lower:
        recommended_roles.append("Entry-Level Data Engineer")
    if "mysql" in resume_lower or "postgresql" in resume_lower or "mongodb" in resume_lower:
        recommended_roles.append("Junior Backend Developer")
    if not recommended_roles:
        recommended_roles.append("Entry-Level Software Developer")

    match_score = int(
        round(
            min(
                100,
                100 * len(matching_skills) / max(len(requested_skills), 1)
            )
        )
    )

    return {
        "match_score": match_score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "recommended_roles": recommended_roles
    }


# ============================================================
# ANALYZE RESUME
# ============================================================

def analyze_resume(
    resume_text,
    job_description,
    resume_file_path=None
):

    resume_content = resume_text

    if not resume_text and resume_file_path:
        resume_content = "The resume is attached as a PDF. Read the resume content from the attached file."

    prompt = f"""
You are an expert AI Resume Analyzer.

Analyze the candidate's resume against the job description.

Return ONLY valid JSON.

Do not add markdown.
Do not add ```json.
Do not add explanations outside JSON.

The JSON must have exactly these fields:

{{
    "match_score": 0,
    "matching_skills": [],
    "missing_skills": [],
    "strengths": [],
    "weaknesses": [],
    "suggestions": [],
    "recommended_roles": []
}}

Rules:

1. match_score must be a number between 0 and 100.

2. matching_skills:
   List skills found in both the resume and job description.

3. missing_skills:
   List important job-description skills that are missing
   or not clearly shown in the resume.

4. strengths:
   List important strengths of the candidate based on the resume.

5. weaknesses:
   List areas where the resume is weaker for this job.

6. suggestions:
   Give practical suggestions to improve the resume
   and job suitability.

7. recommended_roles:
   Suggest suitable job roles based on the resume
   and candidate skills.

RESUME:

{resume_content}

JOB DESCRIPTION:

{job_description}
"""


    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    try:

        response = None
        last_exception = None

        contents = prompt
        if not resume_text and resume_file_path:
            uploaded_resume = client.files.upload(
                file=resume_file_path
            )
            contents = [uploaded_resume, prompt]

        for model_name in MODEL_FALLBACKS:

            for attempt in range(1, MAX_RETRIES + 1):

                try:

                    response = client.models.generate_content(

                        model=model_name,

                        contents=contents,

                        config=types.GenerateContentConfig(

                            temperature=0.2,

                            response_mime_type="application/json"

                        )

                    )

                    break

                except Exception as e:

                    last_exception = e
                    error_text = str(e)
                    print()
                    print(
                        f"Gemini API attempt {attempt} failed for {model_name}:",
                        error_text
                    )

                    if is_retry_error(error_text):

                        if attempt < MAX_RETRIES:

                            wait_time = RETRY_DELAY_SECONDS ** attempt
                            print(
                                f"Retrying in {wait_time} seconds..."
                            )
                            time.sleep(wait_time)
                            continue

                        print(
                            f"Gemini model {model_name} unavailable after {attempt} attempts."
                        )
                        break

                    raise

            if response is not None:
                break

        if response is None:

            error_text = str(last_exception) if last_exception else ""
            print()
            print(
                "GEMINI TEMPORARY UNAVAILABLE: using fallback resume analysis."
            )
            return fallback_analyze_resume(
                resume_text,
                job_description
            )


    except Exception as e:

        print()
        print(
            "GEMINI API ERROR:"
        )

        print(
            e
        )

        print()

        raise


    # ========================================================
    # GET RESPONSE TEXT
    # ========================================================

    response_text = response.text


    if not response_text:

        raise ValueError(
            "Gemini returned an empty response."
        )


    print()
    print(
        "GEMINI RAW RESPONSE:"
    )

    print(
        response_text
    )

    print()


    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    response_text = response_text.strip()


    # Remove markdown JSON blocks if Gemini returns them.

    if response_text.startswith(
        "```"
    ):

        response_text = re.sub(
            r"^```(?:json)?",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        response_text = re.sub(
            r"```$",
            "",
            response_text
        )

        response_text = response_text.strip()


    # ========================================================
    # CONVERT JSON
    # ========================================================

    try:

        result = json.loads(
            response_text
        )


    except json.JSONDecodeError:

        print(
            "JSON ERROR: Gemini returned invalid JSON."
        )

        print(
            response_text
        )

        raise ValueError(
            "Gemini returned invalid JSON."
        )


    # ========================================================
    # CHECK REQUIRED FIELDS
    # ========================================================

    required_fields = [

        "match_score",

        "matching_skills",

        "missing_skills",

        "strengths",

        "weaknesses",

        "suggestions",

        "recommended_roles"

    ]


    for field in required_fields:

        if field not in result:

            result[field] = []


    # ========================================================
    # MATCH SCORE
    # ========================================================

    try:

        score = float(
            result["match_score"]
        )


        score = max(
            0,
            min(
                100,
                score
            )
        )


        if score.is_integer():

            result["match_score"] = int(
                score
            )

        else:

            result["match_score"] = round(
                score,
                2
            )


    except:

        result["match_score"] = 0


    # ========================================================
    # MAKE SURE LIST FIELDS ARE LISTS
    # ========================================================

    list_fields = [

        "matching_skills",

        "missing_skills",

        "strengths",

        "weaknesses",

        "suggestions",

        "recommended_roles"

    ]


    for field in list_fields:

        value = result.get(
            field,
            []
        )


        if isinstance(
            value,
            str
        ):

            result[field] = [

                value

            ]


        elif isinstance(
            value,
            list
        ):

            result[field] = value


        else:

            result[field] = []


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print(
        "FINAL AI RESULT:"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print()


    return result

