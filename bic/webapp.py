from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from typing import Optional

from bic.core import BIC_DB
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction
from bic.__version__ import __version__

# --- App & DB Setup ---
app = FastAPI(
    title="BIC IPAM API",
    description="API and Web UI for the BIC IPAM system.",
    version=__version__,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.middleware("http")
async def add_global_context(request: Request, call_next):
    db = get_db()
    settings = {s['key']: s['value'] for s in db.find_all('settings')}
    request.state.settings = settings
    response = await call_next(request)
    return response

templates.env.globals['settings'] = lambda request: request.state.settings

def get_db():
    return BIC_DB(base_dir=BASE_DIR)

@app.on_event("startup")
def startup_event():
    from bic.modules.firewall_management import setup_nat_rules
    setup_nat_rules()

# --- NEW DYNAMIC UI SYSTEM ---

def find_ui_item_by_path(path: str, menu: UIMenu = menu_structure):
    for item in menu.items:
        if item.path == path:
            return item.item
        if isinstance(item.item, UIMenu):
            found = find_ui_item_by_path(path, item.item)
            if found:
                return found
    return None

def find_action_in_view(view: UIView, action_name_slug: str):
    for action in view.actions:
        if action.name.lower().replace(' ', '-') == action_name_slug:
            return action
    return None

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: BIC_DB = Depends(get_db)):
    from bic.modules import statistics_management
    stats = statistics_management.gather_all_statistics(db)
    clients = db.find_all("clients") 
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats, "clients": clients, "menu": menu_structure})

@app.get("/page/{path:path}", response_class=HTMLResponse)
async def render_page(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    full_path = "/" + path
    ui_item = find_ui_item_by_path(full_path)
    if not ui_item:
        raise HTTPException(status_code=404, detail="Page not found")

    context = {"request": request, "menu": menu_structure, "current_path": full_path}
    if isinstance(ui_item, UIView):
        context["view"] = ui_item
        context["items"] = ui_item.handler(db)
        return templates.TemplateResponse("generic_list.html", context)
    elif isinstance(ui_item, UIAction):
        context["action"] = ui_item

        data = {}
        if ui_item.loader:
            # Handle loaders for direct actions (e.g. from menu) which might need an ID from query params
            item_id = request.query_params.get("id")
            if item_id:
                data = ui_item.loader(db_core=db, id=int(item_id))
            else:
                # This branch handles loaders that don't need an ID (like for creation forms)
                data = ui_item.loader(db_core=db)

        context["data"] = data
        return templates.TemplateResponse("generic_form.html", context)
    else:
        raise HTTPException(status_code=500, detail="Invalid UI item type")

@app.get("/action/{path:path}/{action_name_slug}/{item_id}", response_class=HTMLResponse)
async def render_action_form(request: Request, path: str, action_name_slug: str, item_id: int, db: BIC_DB = Depends(get_db)):
    full_path = "/" + path
    ui_item = find_ui_item_by_path(full_path)

    if not isinstance(ui_item, UIView):
        raise HTTPException(status_code=404, detail="Parent view for action not found")

    action = find_action_in_view(ui_item, action_name_slug)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_name_slug}' not found")

    data = {}
    if action.loader:
        data = action.loader(db_core=db, id=item_id)
        if not data:
            raise HTTPException(status_code=404, detail="Item to edit not found")

    context = {"request": request, "menu": menu_structure, "action": action, "data": data, "current_path": full_path}
    return templates.TemplateResponse("generic_form.html", context)

@app.post("/action/{path:path}", response_class=RedirectResponse)
async def handle_action_post(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    full_path = "/" + path
    ui_item = find_ui_item_by_path(full_path)
    if not ui_item or not isinstance(ui_item, UIAction):
        raise HTTPException(status_code=404, detail="Action not found")
    
    form_data = await request.form()
    try:
        ui_item.handler(db_core=db, **form_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    parent_path = "/".join(full_path.split("/")[:-1])
    return RedirectResponse(url=f"/page{parent_path}", status_code=303)

@app.post("/action/{path:path}/{action_name_slug}/{item_id}", response_class=RedirectResponse)
async def handle_action_item_post(request: Request, path: str, action_name_slug: str, item_id: int, db: BIC_DB = Depends(get_db)):
    full_path = "/" + path
    ui_item = find_ui_item_by_path(full_path)

    if not isinstance(ui_item, UIView):
        raise HTTPException(status_code=404, detail="Parent view for action not found")

    action = find_action_in_view(ui_item, action_name_slug)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_name_slug}' not found")
        
    form_data = await request.form()
    handler_kwargs = {**form_data, "id": item_id}

    try:
        action.handler(db_core=db, **handler_kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    return RedirectResponse(url=f"/page{full_path}", status_code=303)


# --- Client Provisioning Workflow ---

@app.get("/page/clients/provision/new", response_class=HTMLResponse)
async def provision_client_form(request: Request, db: BIC_DB = Depends(get_db)):
    ip_pools = db.find_all("ip_pools")
    return templates.TemplateResponse("provision_client.html", {
        "request": request,
        "ip_pools": ip_pools,
        "menu": menu_structure
    })

@app.post("/action/clients/provision/new")
async def provision_client_action(request: Request, db: BIC_DB = Depends(get_db)):
    form_data = await request.form()
    name = form_data.get("name")
    email = form_data.get("email")
    client_type = form_data.get("client_type")

    assignments = []
    pool_ids = form_data.getlist("assignment_pool_id")
    types = form_data.getlist("assignment_type")
    prefixes = form_data.getlist("assignment_prefix")

    for i in range(len(pool_ids)):
        assignment = {
            "pool_id": int(pool_ids[i]),
            "type": types[i]
        }
        if types[i] == "subnet":
            assignment["prefix_len"] = int(prefixes[i])
        assignments.append(assignment)

    asn = None
    if client_type == "BGP":
        from bic.modules import network_management
        asn = network_management.get_next_available_asn(db)
        if not asn:
            raise HTTPException(status_code=500, detail="No available private ASNs left!")

    from bic.modules import client_management
    result = client_management.provision_new_client(
        db_core=db,
        client_name=name,
        client_email=email,
        client_type=client_type,
        asn=asn,
        assignments=assignments
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "An unknown error occurred during provisioning."))

    return RedirectResponse(url="/page/clients/list", status_code=303)

@app.get("/page/clients/view-configs/{client_id}", response_class=HTMLResponse)
async def view_configs(request: Request, client_id: int, db: BIC_DB = Depends(get_db)):
    client = db.find_one("clients", {"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return templates.TemplateResponse("view_configs.html", {
        "request": request,
        "client": client,
        "menu": menu_structure
    })



# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("webapp:app", host="127.0.0.1", port=8000, reload=True)
