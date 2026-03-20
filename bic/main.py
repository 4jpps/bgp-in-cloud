import uvicorn
import sys
from bic.webapp import app
from bic.log_stream import queue_logger

def run_webapp():
    # Redirect stdout to our queue logger
    sys.stdout = queue_logger
    sys.stderr = queue_logger
    
    print("Starting BIC IPAM - Web App Mode...")
    print(f"API will be available at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_webapp()
