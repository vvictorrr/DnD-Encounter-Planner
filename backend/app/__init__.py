import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import db


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        try:
            db.create_all()
        except OperationalError as e:
            # Multiple processes can race to create the same tables on a
            # fresh boot (e.g. gunicorn workers without --preload, or an
            # old and new instance briefly overlapping during a rolling
            # deploy) - if another process already won that race, the
            # tables exist either way and there's nothing to do here.
            if "already exists" not in str(e).lower():
                raise

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    _register_frontend(app)

    return app


def _register_frontend(app: Flask) -> None:
    """Serve the built React app (if present) so the whole thing runs as a
    single process/container - nothing for a non-technical user to set up
    beyond opening a URL. If the frontend hasn't been built (e.g. plain
    ``npm run dev`` local development, or the backend test suite), the API
    still works fine on its own and this just returns a friendly message.
    """
    dist_dir = app.config["FRONTEND_DIST_DIR"]
    has_frontend = os.path.isdir(dist_dir) and os.path.isfile(os.path.join(dist_dir, "index.html"))

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            # Never let the SPA fallback swallow an unmatched API route.
            return {"error": "not found"}, 404
        if not has_frontend:
            return (
                "The frontend hasn't been built yet. Run `npm run build` in "
                "frontend/ (or use the Docker image, which does this for "
                "you), or run the frontend separately with `npm run dev`.",
                200,
                {"Content-Type": "text/plain"},
            )
        full_path = os.path.join(dist_dir, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, "index.html")