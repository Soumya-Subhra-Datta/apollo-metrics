import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    from backend.config import Config
    config = Config()
    port = int(os.getenv('PORT', 5000))
    if config.ENV == 'production':
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(debug=config.DEBUG, host='0.0.0.0', port=port)
