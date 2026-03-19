import inspect
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException

def filter_strftime(string, fmt):
    if string == "now":
        return datetime.utcnow().strftime(fmt)
    # We can add more logic here to parse date strings if needed
    return string
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

from bic.core import BIC_DB
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction
from bic.modules import system_management
from bic.__version__ import __version__

# --- App and Template Setup ---
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "templates"))
templates.env.filters['strftime'] = filter_strftime

# --- Database Dependency ---
def get_db():
    db = BIC_DB(base_dir=str(BASE_DIR.parent))
    try:
        yield db
    finally:
        db.conn.close()

# --- Helper function to find schema items ---
def find_ui_item_by_path(path: str):
    parts = path.strip("/").split("/")
    current_level = menu_structure.items
    found_item = None
    for part in parts:
        found_item = next((item for item in current_level if item.path.endswith(part)), None)
        if found_item and isinstance(found_item.item, UIMenu):
            current_level = found_item.item.items
        elif found_item:
            break
    return found_item

# --- Main Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: BIC_DB = Depends(get_db)):
    from bic.modules import statistics_management
    settings = system_management.get_all_settings(db)
    stats = statistics_management.gather_all_statistics(db)
    clients = db.find_all("clients")
    return templates.TemplateResponse("dashboard.html", {"request": request, "settings": settings, "stats": stats, "clients": clients, "menu": menu_structure, "version": __version__})

@app.get("/page/{path:path}", response_class=HTMLResponse)
async def render_page(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    # Special redirect for client provisioning
    if path == "clients/provision/new":
        return RedirectResponse(url="/clients/provision/new", status_code=302)
    
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
                data = ui_item.item.loader(db_core=db, id=int(item_id))
            else:
                data = ui_item.item.loader(db_core=db)
        context["data"] = data
        # Process fields for select options
        fields = []
        for field in ui_item.item.form_fields:
            fdict = {
                "name": field.name,
                "label": field.label,
                "type": field.type,
                "required": field.required,
                "options": [],
            }
            if field.type == "select" and field.db_source_table:
                opts = db.find_all(field.db_source_table)
                fdict["options"] = [{"value": opt["id"], "label": opt.get(field.db_source_display_key or "name", str(opt))} for opt in opts]
            fields.append(fdict)
        context["fields"] = fields
        return templates.TemplateResponse("generic_form.html", context)

    raise HTTPException(status_code=404, detail="Invalid page type")

@app.post("/page/{path:path}", response_class=RedirectResponse)
async def handle_form_post(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    ui_item = find_ui_item_by_path(path)
    if not ui_item or not isinstance(ui_item.item, UIAction):
        raise HTTPException(status_code=404, detail="Action not found")
    
    form_data = await request.form()
    form_dict = {k: v for k, v in form_data.items()}
    handler_kwargs = {"db_core": db, **form_dict}
    ui_item.item.handler(**handler_kwargs)
    
    # Convention: after a POST, redirect to the 'list' view for that path.
    path_parts = path.strip("/").split("/")
    path_parts[-1] = "list"
    redirect_path = "/" + "/".join(path_parts)
    
    return RedirectResponse(url=f"/page{redirect_path}", status_code=303)

# --- Special Case Routes ---
@app.get("/clients/provision/new", response_class=HTMLResponse)
async def provision_client_form(request: Request, db: BIC_DB = Depends(get_db)):
    settings = system_management.get_all_settings(db)
    pools = db.find_all("ip_pools")
    return templates.TemplateResponse("provision_client.html", {"request": request, "settings": settings, "pools": pools, "menu": menu_structure, "current_path": "/clients/provision/new", "version": __version__})

@app.post("/clients/provision/new", response_class=RedirectResponse)
async def handle_provision_client(request: Request, db: BIC_DB = Depends(get_db)):
    from bic.modules import client_management
    form_data_raw = await request.form()
    form_dict = {k: v for k, v in form_data_raw.items()}

    # Explicitly pop the required arguments from the dictionary.
    # This ensures they are passed as named arguments and not duplicated in the kwargs.
    client_name = form_dict.pop("client_name", None)
    client_email = form_dict.pop("client_email", None)
    client_type = form_dict.pop("client_type", None)

    # Pass the required arguments by name, and the rest of the form data
    # (like dynamic assignments) as keyword arguments.
    client_management.provision_new_client(
        db_core=db,
        client_name=client_name,
        client_email=client_email,
        client_type=client_type,
        **form_dict  # The rest of the form items are passed here
    )
    return RedirectResponse(url="/page/clients/list", status_code=303)

@app.get("/system/statistics", response_class=HTMLResponse)
async def system_stats_page(request: Request, db: BIC_DB = Depends(get_db)):
    settings = system_management.get_all_settings(db)
    from bic.modules import statistics_management
    stats = statistics_management.gather_all_statistics(db)
    return templates.TemplateResponse("system_statistics.html", {"request": request, "settings": settings, "stats": stats, "menu": menu_structure, "current_path": "/system/statistics", "version": __version__})

@app.on_event("startup")
async def startup_event():
    from bic.modules import firewall_management
    print("  -> Ensuring NAT rules for private ranges...")
    firewall_management.ensure_nat_rules()
