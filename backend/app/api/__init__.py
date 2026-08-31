from flask import Blueprint

api_bp = Blueprint("api", __name__)

# Route modules register themselves onto api_bp on import.
from . import campaigns  # noqa: E402,F401
from . import reference  # noqa: E402,F401
from . import simulate  # noqa: E402,F401
