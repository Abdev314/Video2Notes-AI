from flask import Flask
from flask_cors import CORS
from .routes import bp   # ← important: dot here

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config["UPLOAD_FOLDER"] = "data"
    app.config["OUTPUT_FOLDER"] = "output"
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2GB

    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)