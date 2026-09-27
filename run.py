"""Convenience runner script for Safe Wealth Advisory."""
import os
import sys

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.join(_ROOT_DIR, "backend")

for p in [_ROOT_DIR, _BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    app.run(host="0.0.0.0", port=port, debug=debug)
