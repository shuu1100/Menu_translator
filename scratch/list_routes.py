import sys
sys.path.insert(0, ".")
from backend.app.main import app

openapi = app.openapi()
print("=== OPENAPI ENDPOINTS ===")
for path, methods in sorted(openapi.get("paths", {}).items()):
    for method, details in methods.items():
        summary = details.get("summary", details.get("description", ""))
        print(f"[{method.upper():<6}] http://127.0.0.1:8001{path} -> {summary}")
