import os


class Config:
    """Base config. Overridden by env vars in real deployments."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "campaigns.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Where the *built* frontend (npm run build output) lives, if anywhere.
    # Defaults to ../../frontend/dist relative to this file, i.e. a sibling
    # `frontend/dist` folder in the same repo checkout - matches both a
    # local "build once, run one Python process" setup and the combined
    # Docker image (see the root Dockerfile), with no env var required in
    # either case. If the folder doesn't exist, the app still runs fine as
    # an API-only server (e.g. `npm run dev` local development).
    FRONTEND_DIST_DIR = os.environ.get(
        "FRONTEND_DIST_DIR",
        os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "dist")),
    )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
