
import os
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config

from database import (
    get_connection,
    create_tables,
    save_resume_history,
    get_resume_history,
    get_resume_history_item
)

from resume_parser import extract_text
from ai_analyzer import analyze_resume




app = Flask(__name__)
app.secret_key = Config.SECRET_KEY


UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {"pdf", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

create_tables()


# =========================================================
# CREATE HISTORY TABLE IF IT DOES NOT EXIST
# =========================================================

def ensure_history_table():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                job_description TEXT,
                match_score INT DEFAULT 0,
                matching_skills TEXT,
                missing_skills TEXT,
                strengths TEXT,
                weaknesses TEXT,
                suggestions TEXT,
                recommended_roles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    except Exception as e:
        print("HISTORY TABLE ERROR:", e)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


ensure_history_table()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def login_required():

    return "user_id" in session


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:

            flash("All fields are required.", "error")

            return redirect(url_for("register"))

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                flash("Email already registered.", "error")

                return redirect(url_for("register"))

            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            connection.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            print("REGISTER ERROR:", e)

            flash(
                "Registration failed.",
                "error"
            )

            return redirect(url_for("register"))

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("register.html")


# =========================================================
# REGISTER SUCCESS
# =========================================================

@app.route("/register_success")
def register_success():

    return render_template("register_success.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password"],
                password
            ):

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]

                return redirect(
                    url_for("dashboard")
                )

            flash(
                "Invalid email or password.",
                "error"
            )

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash(
                "Login failed. Please try again.",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        name=session.get("user_name")
    )


# =========================================================
# ANALYZE PAGE
# =========================================================

@app.route("/analyze")
def analyze():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "analyze.html",
        result=session.get("analysis_result")
    )


# =========================================================
# UPLOAD RESUME + JOB DESCRIPTION
# =========================================================

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    if not login_required():

        return redirect(
            url_for("login")
        )

    try:

        # -------------------------------------------------
        # RESUME FILE
        # -------------------------------------------------

        resume_file = request.files.get("resume")

        if not resume_file or resume_file.filename == "":

            flash(
                "Please upload a resume PDF.",
                "error"
            )

            return redirect(
                url_for("analyze")
            )

        if not allowed_file(
            resume_file.filename
        ):

            flash(
                "Resume must be a PDF file.",
                "error"
            )

            return redirect(
                url_for("analyze")
            )

        filename = secure_filename(
            resume_file.filename
        )

        # Avoid duplicate filenames

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        resume_file.save(filepath)


        # -------------------------------------------------
        # EXTRACT RESUME TEXT
        # -------------------------------------------------

        resume_text = extract_text(
            filepath
        )

        print(
            f"RESUME EXTRACTED: filename={filename}, characters={len(resume_text or '')}"
        )

        if not resume_text or not resume_text.strip():
            print(
                "RESUME HAS NO EMBEDDED TEXT: sending the PDF directly to Gemini."
            )


        # -------------------------------------------------
        # JOB DESCRIPTION TEXT
        # -------------------------------------------------

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        print(
            f"JOB DESCRIPTION FORM: characters={len(job_description)}"
        )


        # -------------------------------------------------
        # JOB DESCRIPTION PDF
        # -------------------------------------------------

        job_file = request.files.get(
            "job_description_file"
        )

        if job_file and job_file.filename:

            if not allowed_file(
                job_file.filename
            ):

                flash(
                    "Job description file must be a PDF.",
                    "error"
                )

                return redirect(
                    url_for("analyze")
                )

            job_filename = secure_filename(
                job_file.filename
            )

            job_filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                "job_" + job_filename
            )

            job_file.save(job_filepath)

            extracted_job_text = extract_text(
                job_filepath
            )

            if extracted_job_text:

                job_description = extracted_job_text.strip()

            print(
                f"JOB DESCRIPTION FILE: filename={job_filename}, characters={len(extracted_job_text or '')}"
            )


        # -------------------------------------------------
        # CHECK JOB DESCRIPTION
        # -------------------------------------------------

        if not job_description:

            print(
                "UPLOAD REJECTED: no job description text was provided."
            )

            flash(
                "Please paste a job description or upload a job description PDF.",
                "error"
            )

            return redirect(
                url_for("analyze")
            )


        # -------------------------------------------------
        # AI ANALYSIS
        # -------------------------------------------------

        result = analyze_resume(
            resume_text,
            job_description,
            filepath
        )

        print("\n")
        print("=" * 60)
        print("AI ANALYSIS RESULT")
        print("=" * 60)
        print(json.dumps(
            result,
            indent=4,
            default=str
        ))
        print("=" * 60)


        # -------------------------------------------------
        # SAVE RESULT IN SESSION
        # -------------------------------------------------

        session.pop("analysis_result", None)
        session.pop("job_description", None)
        session["resume_filename"] = filename


        # -------------------------------------------------
        # SAVE HISTORY
        # -------------------------------------------------

        try:

            history_id = save_resume_history(
                user_id=session["user_id"],
                filename=filename,
                job_description=job_description,
                result=result
            )

            session["analysis_id"] = history_id

            print(
                "HISTORY SAVED SUCCESSFULLY"
            )

        except Exception as history_error:

            print(
                "HISTORY SAVE ERROR:",
                history_error
            )

            # Analysis should still work even
            # if history saving fails.

        flash(
            "Resume analyzed successfully.",
            "success"
        )

        return redirect(
            url_for("result")
        )


    except Exception as e:

        print("\n")
        print("=" * 60)
        print("UPLOAD / AI ERROR")
        print("=" * 60)
        print(e)
        print("=" * 60)

        error_text = str(e).upper()
        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
            or "HIGH DEMAND" in error_text
            or "TEMPORARY" in error_text
        ):
            flash(
                "AI analysis failed because Gemini is temporarily unavailable due to high demand. Please try again later.",
                "error"
            )
        else:
            flash(
                "AI analysis failed. Please check your resume, job description and Gemini API configuration.",
                "error"
            )

        return redirect(
            url_for("analyze")
        )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    if not login_required():

        return redirect(
            url_for("login")
        )

    try:

        history_data = get_resume_history(
            session["user_id"]
        )

        return render_template(
            "history.html",
            analyses=history_data
        )

    except Exception as e:

        print(
            "HISTORY ERROR:",
            e
        )

        flash(
            "Could not load analysis history.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


# =========================================================
# JOB RECOMMENDATIONS
# =========================================================

@app.route("/jobs")
def jobs():

    if not login_required():

        return redirect(
            url_for("login")
        )

    result = get_resume_history_item(
        session["user_id"],
        session.get("analysis_id")
    ) if session.get("analysis_id") else None

    if not result:

        flash(
            "Please analyze a resume first.",
            "error"
        )

        return redirect(
            url_for("analyze")
        )

    recommended_roles = result.get(
        "recommended_roles",
        []
    )

    missing_skills = result.get(
        "missing_skills",
        []
    )

    matching_skills = result.get(
        "matching_skills",
        []
    )

    match_score = result.get(
        "match_score",
        0
    )

    return render_template(
        "jobs.html",
        recommended_roles=recommended_roles,
        missing_skills=missing_skills,
        matching_skills=matching_skills,
        match_score=match_score
    )


# =========================================================
# RESULT PAGE
# =========================================================

@app.route("/result")
def result():

    if not login_required():

        return redirect(
            url_for("login")
        )

    analysis_result = get_resume_history_item(
        session["user_id"],
        session.get("analysis_id")
    ) if session.get("analysis_id") else None

    if not analysis_result:

        flash(
            "No analysis result available.",
            "error"
        )

        return redirect(
            url_for("analyze")
        )

    return render_template(
        "result.html",
        result=analysis_result
    )


# =========================================================
# CLEAR CURRENT ANALYSIS
# =========================================================

@app.route("/clear_analysis")
def clear_analysis():

    if not login_required():

        return redirect(
            url_for("login")
        )

    session.pop(
        "analysis_id",
        None
    )

    session.pop(
        "resume_filename",
        None
    )

    session.pop(
        "job_description",
        None
    )

    flash(
        "Current analysis cleared.",
        "success"
    )

    return redirect(
        url_for("analyze")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )


