# AI Resume Analyzer & Job Matcher

An AI-powered web application that analyzes resumes and compares them with job descriptions to identify matching skills, missing skills, and an overall match percentage.

## Features

* Resume PDF upload and text extraction
* AI-based resume analysis
* Job description analysis
* Resume and job matching
* Matching skills identification
* Missing skills identification
* Improvement suggestions
* User registration and login
* Analysis history
* Dashboard for previous analyses

## Technologies Used

* Python
* Flask
* MySQL
* HTML
* CSS
* JavaScript
* Gemini API
* PyPDF2

## Project Structure

```text
AI_RESUME_ANALYZER/
│
├── app.py
├── ai_analyzer.py
├── resume_parser.py
├── database.py
├── config.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── analyze.html
│   ├── result.html
│   └── history.html
│
└── uploads/
```

## How It Works

1. User uploads a resume in PDF format.
2. The application extracts text from the resume.
3. User provides a job description.
4. The AI analyzes the resume and job requirements.
5. The application identifies matching and missing skills.
6. A match percentage and improvement suggestions are displayed.

## Installation

Clone the repository:

```bash
git clone https://github.com/venprv77/ai_resume_analyzer.git
```

Go to the project folder:

```bash
cd ai_resume_analyzer
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables and database settings.

Run the application:

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## Purpose

This project was developed as a practical AI and web development project to demonstrate skills in Python, Flask, MySQL, web development, PDF processing, and Generative AI.
