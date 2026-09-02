"""Launch Noor. Localhost only: there is no authentication (SSOT §6)."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("noor.web.app:app", host="127.0.0.1", port=8000, app_dir="src")
