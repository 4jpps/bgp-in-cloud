import inspect
import asyncio
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pathlib import Path

from bic.core import BIC_DB
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction
from bic.modules import system_management, statistics_management, update_management
from bic.__version__ import __version__

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "templates"))

# In-memory cache for update info
update_cache = {
    "new_version": None,
    "changelog": None,
    "last_checked": None
}

def get_db():
    db = BIC_DB(base_dir=str(BASE_DIR.parent))
    try: yield db
    finally: db.conn.close()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: BIC_DB = Depends(get_db)):
    settings = system_management.get_all_settings(db)
    stats = statistics_management.gather_all_statistics(db)
    clients = db.find_all("clients")
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "settings": settings, 
        "stats": stats, 
        "clients": clients, 
        "menu": menu_structure, 
        "version": __version__
    })

@app.get("/api/perform-update", response_class=JSONResponse)
async def perform_update_api():
    result = update_management.perform_update()
    return result


@app.get("/api/check-update", response_class=JSONResponse)
async def check_update_api():
    return {
        "update_available": update_cache["new_version"] is not None,
        "new_version": update_cache["new_version"],
        "changelog": update_cache["changelog"]
    }

async def periodic_update_check():
    while True:
        # Check every 6 hours
        if not update_cache["last_checked"] or datetime.now() - update_cache["last_checked"] > timedelta(hours=6):
            print("Checking for application updates...")
            # Create a new DB instance within this thread
            db = BIC_DB(base_dir=str(BASE_DIR.parent))
            new_version, changelog = update_management.is_update_available(db)
            if new_version:
                print(f"New version found: {new_version}")
                update_cache["new_version"] = new_version
                update_cache["changelog"] = changelog
            else:
                print("Application is up to date.")
            update_cache["last_checked"] = datetime.now()
            db.conn.close() # Close the connection for this thread
        await asyncio.sleep(3600) # Check again in 1 hour

@app.on_event("startup")
async def startup_event():
    from bic.modules import firewall_management
    print("  -> Ensuring NAT rules for private ranges...")
    firewall_management.ensure_nat_rules()
    # Start the background task
    asyncio.create_task(periodic_update_check())

# ... (rest of the webapp code) ...
