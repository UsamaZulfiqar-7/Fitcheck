"""Runner script for the FitCheck REST API server.

Run with:
    python run_api.py

Access Swagger Documentation:
    http://127.0.0.1:8000/docs
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("Starting FitCheck Pipeline API Server...")
    print("Architecture: Jobs (PDF/Image/Text) -> API -> Storage -> Processing -> Analyzing -> Serving")
    print("OpenAPI Docs available at: http://127.0.0.1:8000/docs")
    print("=" * 70)
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
