import os
import logging
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.database.db import init_db
from backend.routes.auth_routes import auth_bp
from backend.routes.upload_routes import upload_bp
from backend.routes.eda_routes import eda_bp
from backend.routes.chart_routes import chart_bp
from backend.routes.ml_routes import ml_bp
from backend.routes.query_routes import query_bp
from backend.routes.report_routes import report_bp
from backend.routes.dashboard_routes import dashboard_bp


def create_app():
    app = Flask(__name__)
    config = Config()
    app.secret_key = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    app.config['ENV'] = config.ENV
    app.config['DEBUG'] = config.DEBUG
    app.config['SESSION_COOKIE_SECURE'] = config.ENV == 'production'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    logging.basicConfig(
        level=logging.DEBUG if config.DEBUG else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Apollo Metrics in {config.ENV} mode")

    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(eda_bp)
    app.register_blueprint(chart_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)

    for folder in [config.UPLOAD_FOLDER, config.CLEANED_FOLDER, config.MODELS_FOLDER, config.REPORTS_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    try:
        init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'The requested resource was not found.'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Internal server error")
        return jsonify({'error': 'An internal server error occurred.'}), 500

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'error': 'File is too large. Maximum size is 50MB.'}), 413

    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/upload')
    def upload_page():
        return render_template('upload.html')

    @app.route('/eda')
    def eda_page():
        return render_template('eda.html')

    @app.route('/charts')
    def charts_page():
        return render_template('charts.html')

    @app.route('/ml')
    def ml_page():
        return render_template('ml.html')

    @app.route('/query')
    def query_page():
        return render_template('query.html')

    @app.route('/reports')
    def reports_page():
        return render_template('reports.html')

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'env': config.ENV}), 200

    @app.route('/static/<path:path>')
    def serve_static(path):
        response = send_from_directory('static', path)
        if not config.DEBUG:
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
