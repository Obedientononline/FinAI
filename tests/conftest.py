import os
import sys

# Ensure root and backend directories are in sys.path for test execution
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_TESTS_DIR)
_BACKEND_DIR = os.path.join(_ROOT_DIR, "backend")

for p in [_ROOT_DIR, _BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)
