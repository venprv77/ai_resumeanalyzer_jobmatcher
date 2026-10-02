
import mysql.connector
from config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=getattr(Config, "DB_PORT", 3306),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Resume history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            filename VARCHAR(255),
            job_description TEXT,
            match_score INT DEFAULT 0,
            matching_skills TEXT,
            missing_skills TEXT,
            strengths TEXT,
            weaknesses TEXT,
            suggestions TEXT,
            recommended_roles TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


def save_resume_history(
    user_id,
    filename,
    job_description,
    result
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO resume_history
        (
            user_id,
            filename,
            job_description,
            match_score,
            matching_skills,
            missing_skills,
            strengths,
            weaknesses,
            suggestions,
            recommended_roles
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        user_id,
        filename,
        job_description,
        result.get("match_score", 0),
        ", ".join(result.get("matching_skills", [])),
        ", ".join(result.get("missing_skills", [])),
        " | ".join(result.get("strengths", [])),
        " | ".join(result.get("weaknesses", [])),
        " | ".join(result.get("suggestions", [])),
        ", ".join(result.get("recommended_roles", []))
    )

    cursor.execute(query, values)

    connection.commit()

    history_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return history_id


def get_resume_history(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            filename,
            job_description,
            match_score,
            matching_skills,
            missing_skills,
            strengths,
            weaknesses,
            suggestions,
            recommended_roles,
            created_at
        FROM resume_history
        WHERE user_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (user_id,))

    history = cursor.fetchall()

    cursor.close()
    connection.close()

    return history


def get_resume_history_item(user_id, history_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            filename,
            job_description,
            match_score,
            matching_skills,
            missing_skills,
            strengths,
            weaknesses,
            suggestions,
            recommended_roles,
            created_at
        FROM resume_history
        WHERE user_id = %s AND id = %s
    """

    cursor.execute(query, (user_id, history_id))
    history_item = cursor.fetchone()

    cursor.close()
    connection.close()

    if not history_item:
        return None

    history_item["matching_skills"] = split_history_value(
        history_item["matching_skills"], ","
    )
    history_item["missing_skills"] = split_history_value(
        history_item["missing_skills"], ","
    )
    history_item["strengths"] = split_history_value(
        history_item["strengths"], "|"
    )
    history_item["weaknesses"] = split_history_value(
        history_item["weaknesses"], "|"
    )
    history_item["suggestions"] = split_history_value(
        history_item["suggestions"], "|"
    )
    history_item["recommended_roles"] = split_history_value(
        history_item["recommended_roles"], ","
    )

    return history_item


def split_history_value(value, separator):
    if not value:
        return []

    return [item.strip() for item in value.split(separator) if item.strip()]

