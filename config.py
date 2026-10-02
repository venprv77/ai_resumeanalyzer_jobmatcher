# import os


# class Config:

#     # Flask
#     SECRET_KEY = "ai_resume_analyzer_secret_key_2026"


#     # MySQL
#     DB_HOST = "127.0.0.1"

#     DB_PORT = 3306

#     DB_USER = "root"

#     DB_PASSWORD = "moksha"

#     DB_NAME = "ai_resume_analyzer"


#     # Upload folders
#     UPLOAD_FOLDER = "uploads"

#     REPORT_FOLDER = "reports"


import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "your-secret-key"
    )

    GEMINI_API_KEY = os.environ.get(
        "GEMINI_API_KEY",
        "YOUR_GEMINI_API_KEY_HERE"
    )

    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = "moksha"
    DB_NAME = "ai_resume_analyzer"