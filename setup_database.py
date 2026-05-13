"""
Apollo Metrics - Automatic Database Setup Script

Run this script to create the MySQL database and all required tables.
Usage: python setup_database.py
"""

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'apollo_metrics')

REQUIRED_FOLDERS = [
    'uploads',
    'cleaned',
    'models',
    'reports'
]

TABLES_SQL = {
    'users': """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'uploads': """
        CREATE TABLE IF NOT EXISTS uploads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            total_rows INT DEFAULT 0,
            total_columns INT DEFAULT 0,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'analysis_history': """
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            upload_id INT NOT NULL,
            user_id INT NOT NULL,
            summary TEXT,
            missing_value_report TEXT,
            outlier_report TEXT,
            cleaned_file_path VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'user_queries': """
        CREATE TABLE IF NOT EXISTS user_queries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            upload_id INT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'model_results': """
        CREATE TABLE IF NOT EXISTS model_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            upload_id INT NOT NULL,
            target_column VARCHAR(255),
            task_type VARCHAR(50),
            model_name VARCHAR(255),
            metrics TEXT,
            model_path VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'reports': """
        CREATE TABLE IF NOT EXISTS reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            upload_id INT NOT NULL,
            report_name VARCHAR(255),
            report_path VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
}


def print_status(message, success=True):
    icon = "OK" if success else "FAIL"
    print(f"  [{icon}] {message}")


def setup_database():
    print("\n" + "=" * 60)
    print("  Apollo Metrics - Database Setup")
    print("=" * 60 + "\n")

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        print_status("Database connected successfully.")
    except mysql.connector.Error as err:
        print(f"\n  [FAIL] Could not connect to MySQL: {err}")
        print("  Please check your .env file and ensure MySQL is running.")
        return False

    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print_status(f"Database '{DB_NAME}' created or already exists.")
    except mysql.connector.Error as err:
        print_status(f"Could not create database: {err}", False)
        cursor.close()
        conn.close()
        return False

    cursor.execute(f"USE {DB_NAME}")

    success_count = 0
    for table_name, create_sql in TABLES_SQL.items():
        try:
            cursor.execute(create_sql)
            print_status(f"'{table_name}' table ready.")
            success_count += 1
        except mysql.connector.Error as err:
            print_status(f"Could not create '{table_name}': {err}", False)

    cursor.close()
    conn.close()

    if success_count == len(TABLES_SQL):
        print_status(f"All {success_count} tables created successfully.")
    else:
        print(f"\n  [WARN] Created {success_count}/{len(TABLES_SQL)} tables. Check errors above.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    created_folders = 0
    for folder in REQUIRED_FOLDERS:
        folder_path = os.path.join(base_dir, folder)
        try:
            os.makedirs(folder_path, exist_ok=True)
            print_status(f"Folder '{folder}/' ready.")
            created_folders += 1
        except Exception as e:
            print_status(f"Could not create folder '{folder}': {e}", False)

    if created_folders == len(REQUIRED_FOLDERS):
        print_status("Required folders created successfully.")

    print("\n" + "-" * 60)
    if success_count == len(TABLES_SQL):
        print("  Database setup completed successfully.")
    else:
        print("  Database setup completed with some warnings.")
    print("=" * 60 + "\n")
    return True


if __name__ == '__main__':
    setup_database()
