import mysql.connector
from backend.config import Config


def _get_ssl_config(config):
    if config.MYSQL_SSL_CA:
        return {'ca': config.MYSQL_SSL_CA}
    return {}


def get_db_connection():
    config = Config()
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            ssl_ca=_get_ssl_config(config).get('ca')
        )
        return conn
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")


def init_db():
    config = Config()
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            ssl_ca=_get_ssl_config(config).get('ca')
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()

        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            ssl_ca=_get_ssl_config(config).get('ca')
        )
        cursor = conn.cursor()

        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        }

        for table_name, create_sql in tables.items():
            cursor.execute(create_sql)

        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        raise Exception(f"Database initialization failed: {err}")
