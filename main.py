# main.py
# The entry point for the application. This script starts the backend server.

import uvicorn

if __name__ == "__main__":
    # Run the FastAPI server using uvicorn
    # --reload will make the server restart on code changes, which is great for development
    uvicorn.run("core.server:app", host="0.0.0.0", port=8000, reload=True)
