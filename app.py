"""Safe Wealth Advisory & Governed Portfolio Rebalancer.

Root entrypoint exposing the application for local execution, Gunicorn, and Docker containers.
Delegates to backend.app.
"""
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
    print("\n  =======================================================")
    print("  🏛️ Safe Wealth Advisory & Governed Portfolio Rebalancer")
    print(f"  🚀 Server running at: http://localhost:{port}")
    print("  =======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
