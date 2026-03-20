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

def find_ui_item_by_path(path: str, menu_to_search: UIMenu = menu_structure):
    """Recursively search for a UI item by its path."""
    for item in menu_to_search.items:
        if item.path and item.path.strip('/') == path.strip('/'):
            return item
        if isinstance(item.item, UIMenu):
            found_in_submenu = find_ui_item_by_path(path, item.item)
            if found_in_submenu:
                return found_in_submenu
    return None

@app.get("/page/{path:path}", response_class=HTMLResponse)
async def render_page(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    settings = system_management.get_all_settings(db)
    ui_item = find_ui_item_by_path(path)
    if not ui_item or not ui_item.item:
        raise HTTPException(status_code=404, detail="Page not found")

    if isinstance(ui_item.item, UIMenu):
        context = {"request": request, "settings": settings, "item": ui_item.item, "menu": menu_structure, "current_path": path, "version": __version__}
        return templates.TemplateResponse("generic_menu.html", context)

    if isinstance(ui_item.item, UIView):
        context = {"request": request, "settings": settings, "view": ui_item.item, "menu": menu_structure, "current_path": path, "version": __version__}
        items = ui_item.item.handler(db)
        context["items"] = items
        return templates.TemplateResponse("generic_list.html", context)

    elif isinstance(ui_item.item, UIAction):
        context = {"request": request, "settings": settings, "action": ui_item.item, "menu": menu_structure, "current_path": path, "version": __version__}
        data = {}
        if ui_item.item.loader:
            item_id = request.query_params.get("id")
            if item_id:
                data = ui_item.item.loader(db_core=db, id=item_id)
            else:
                data = ui_item.item.loader(db_core=db)
        context["data"] = data
        for field in ui_item.item.form_fields:
            if field.type == "select" and field.options_loader:
                field.options = field.options_loader(db)
        if ui_item.item.actions:
            for sub_action_item in ui_item.item.actions:
                for field in sub_action_item.item.form_fields:
                    if field.type == "select" and field.options_loader:
                        field.options = field.options_loader(db)
        pools = db.find_all("ip_pools")
        context["pools_json"] = json.dumps(pools)
        return templates.TemplateResponse("generic_form.html", context)

    raise HTTPException(status_code=404, detail="Invalid page type")

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
        if not update_cache["last_checked"] or datetime.now() - update_cache["last_checked"] > timedelta(hours=6):
            print("Checking for application updates...")
            db = BIC_DB(base_dir=str(BASE_DIR.parent))
            new_version, changelog = update_management.is_update_available(db)
            if new_version:
                print(f"New version found: {new_version}")
                update_cache["new_version"] = new_version
                update_cache["changelog"] = changelog
            else:
                print("Application is up to date.")
            update_cache["last_checked"] = datetime.now()
            db.conn.close()
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    from bic.modules import firewall_management
    print("  -> Ensuring NAT rules for private ranges...")
    firewall_management.ensure_nat_rules()
    asyncio.create_task(periodic_update_check())
