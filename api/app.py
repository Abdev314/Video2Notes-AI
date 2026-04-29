from flask import Flask, send_from_directory, request
from flask_cors import CORS
from .routes import bp  # Your API routes
import os


def create_app():
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))

    app = Flask(
        __name__,
        static_folder=frontend_path,
        static_url_path=""
    )

    # Only enable CORS for API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config["UPLOAD_FOLDER"] = "data"
    app.config["OUTPUT_FOLDER"] = "output"
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

    # ✅ KEY FIX: Prefix blueprint routes with /api
    app.register_blueprint(bp, url_prefix="/api")

    # ✅ Serve Vue index.html at root
    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_path, "index.html")

    # ✅ Catch-all for Vue Router (registered LAST)
    @app.route("/<path:path>")
    def catch_all(path):
        # ✅ Skip API routes - let blueprint handle them
        if path.startswith("api/"):
            return {"error": "API route not found"}, 404

        # ✅ If it's a real static file (JS/CSS/img), serve it
        file_path = os.path.join(frontend_path, path)
        if os.path.isfile(file_path):
            return send_from_directory(frontend_path, path)

        # ✅ Otherwise, serve index.html for Vue Router to handle client-side routes
        return send_from_directory(frontend_path, "index.html")

    # ✅ Add cache-control headers to prevent stale loads
    @app.after_request
    def add_cache_headers(response):
        if request.path.endswith('.html') or request.path == '/':
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)