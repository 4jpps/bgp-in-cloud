
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import importlib
from typing import Optional

from bic.core import BIC_DB
from bic.modules import statistics_management, settings_management
from bic.menus.menu_structure import MENU_STRUCTURE
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
templates.env.globals['MENU_STRUCTURE'] = MENU_STRUCTURE
templates.env.globals['settings'] = settings_management.get_all_settings(BIC_DB(base_dir=BASE_DIR))

def get_db():
    return BIC_DB(base_dir=BASE_DIR)

@app.on_event("startup")
def startup_event():
    # This ensures the DB is initialized when the app starts.
    get_db()


# --- Helper Functions ---
def find_action_def(action_path: str):
    """
    Traverses the MENU_STRUCTURE dictionary based on a hyphenated path.
    e.g., "client-management/add-new-client"
    """
    keys = [key.replace("-", " ") for key in action_path.split("/")]
    current_level = MENU_STRUCTURE
    for key in keys:
        if current_level.get(key):
            current_level = current_level[key]
            if current_level.get('type') == 'submenu':
                current_level = current_level['handler']
        else:
            return None
    return current_level

def get_full_action_path(menu_item, current_path=""):
    # This is a helper that could be used to generate paths, not used in the final version
    # but good for understanding the structure.
    pass


# --- Web UI Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: BIC_DB = Depends(get_db)):
    stats = statistics_management.gather_all_statistics(db)
    clients = db.find_all("clients") 
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "stats": stats, 
        "clients": clients,
        "menu": MENU_STRUCTURE
    })

@app.get("/clients", response_class=HTMLResponse)
async def get_clients(request: Request, db: BIC_DB = Depends(get_db)):
    clients = db.find_all("clients")
    return templates.TemplateResponse("clients.html", {"request": request, "clients": clients})

@app.get("/network/pools", response_class=HTMLResponse)
async def get_pools(request: Request, db: BIC_DB = Depends(get_db)):
    pools = db.find_all("ip_pools")
    return templates.TemplateResponse("pools.html", {"request": request, "pools": pools})

@app.get("/clients/add", response_class=HTMLResponse)
async def add_client_form(request: Request):
    return templates.TemplateResponse("client_form.html", {"request": request, "title": "Add Client"})

@app.post("/clients/add", response_class=RedirectResponse)
async def add_client(name: str = Form(...), email: str = Form(None), asn: int = Form(None), allow_smtp: bool = Form(False), db: BIC_DB = Depends(get_db)):
    db.insert("clients", {"name": name, "email": email, "asn": asn, "allow_smtp": allow_smtp})
    return RedirectResponse(url="/clients", status_code=303)

@app.get("/network/pools/add", response_class=HTMLResponse)
async def add_pool_form(request: Request):
    return templates.TemplateResponse("pool_form.html", {"request": request, "title": "Add IP Pool"})

@app.post("/network/pools/add", response_class=RedirectResponse)
async def add_pool(name: str = Form(...), cidr: str = Form(...), afi: str = Form(...), description: str = Form(None), db: BIC_DB = Depends(get_db)):
    db.insert("ip_pools", {"name": name, "cidr": cidr, "afi": afi, "description": description})
    return RedirectResponse(url="/network/pools", status_code=303)

import importlib

# The find_action_def and generic action routes need to be defined
def find_action_def(menu, handler_path):
    for key, value in menu.items():
        if value['type'] == 'action' and value.get('handler') == handler_path:
            return value
        elif value['type'] == 'submenu':
            found = find_action_def(value['handler'], handler_path)
            if found:
                return found
    return None

@app.get("/action/{action_path:path}", response_class=HTMLResponse)
async def get_action_form(request: Request, action_path: str, db: BIC_DB = Depends(get_db)):
    action_def = find_action_def(MENU_STRUCTURE, action_path)
    
    if not action_def or 'web_form' not in action_def:
        raise HTTPException(status_code=404, detail="Action not found or has no web form")

    title = action_path.replace('bic.menus.','').replace('.', ' ').title()
    form_fields = action_def.get('web_form', [])

    for field in form_fields:
        if field.get('type') == 'select_from_db':
            field['options'] = db.find_all(field['source'])

    return templates.TemplateResponse("generic_action_form.html", {
        "request": request,
        "title": title,
        "form_fields": form_fields,
        "action_path": action_path
    })

@app.post("/action/{action_path:path}")
async def post_action_form(request: Request, action_path: str, db: BIC_DB = Depends(get_db)):
    action_def = find_action_def(MENU_STRUCTURE, action_path)

    if not action_def or 'web_handler' not in action_def:
        raise HTTPException(status_code=404, detail="Action not found or has no web handler")

    form_data = await request.form()
    data = {k: v for k, v in form_data.items()}

    handler_path = action_def['web_handler']
    module_path, function_name = handler_path.rsplit('.', 1)

    try:
        module = importlib.import_module(module_path)
        handler_function = getattr(module, function_name)
        handler_function(db_core=db, **data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    # This is a simplification; a real app might have more complex redirect logic
    return RedirectResponse(url="/", status_code=303)

@app.get("/network/pool/{pool_id}/edit", response_class=HTMLResponse)
async def edit_pool_form(request: Request, pool_id: int, db: BIC_DB = Depends(get_db)):
    pool = db.find_one("ip_pools", {"id": pool_id})
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return templates.TemplateResponse("pool_form.html", {"request": request, "title": f"Edit IP Pool: {pool['name']}", "pool": pool})

@app.post("/network/pool/{pool_id}/edit", response_class=RedirectResponse)
async def edit_pool(pool_id: int, name: str = Form(...), cidr: str = Form(...), afi: str = Form(...), description: str = Form(None), db: BIC_DB = Depends(get_db)):
    db.update("ip_pools", pool_id, {"name": name, "cidr": cidr, "afi": afi, "description": description})
    return RedirectResponse(url="/network/pools", status_code=303)

@app.get("/network/pool/{pool_id}/delete", response_class=RedirectResponse)
async def delete_pool(pool_id: int, db: BIC_DB = Depends(get_db)):
    db.delete("ip_pools", pool_id)
    return RedirectResponse(url="/network/pools", status_code=303)

@app.get("/client/{client_id}/edit", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: int, db: BIC_DB = Depends(get_db)):
    client = db.find_one("clients", {"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return templates.TemplateResponse("client_form.html", {"request": request, "title": f"Edit Client: {client['name']}", "client": client})

@app.post("/client/{client_id}/edit", response_class=RedirectResponse)
async def edit_client(client_id: int, name: str = Form(...), email: str = Form(None), asn: int = Form(None), allow_smtp: bool = Form(False), db: BIC_DB = Depends(get_db)):
    db.update("clients", client_id, {"name": name, "email": email, "asn": asn, "allow_smtp": allow_smtp})
    return RedirectResponse(url=f"/client/{client_id}", status_code=303)

@app.get("/client/{client_id}/delete", response_class=RedirectResponse)
async def delete_client(client_id: int, db: BIC_DB = Depends(get_db)):
    from bic.modules import client_management # Local import to avoid circular dependencies
    client_management.deprovision_and_delete_client(db_core=db, client_id=client_id)
    return RedirectResponse(url="/clients", status_code=303)





# --- Detail Views (These are not dynamically generated) ---
@app.get("/client/{client_id}", response_class=HTMLResponse)
async def client_detail(request: Request, client_id: int, db: BIC_DB = Depends(get_db)):
    client = db.find_one("clients", {"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    ips = db.find_all_by("ip_allocations", {"client_id": client_id})
    subnets = db.find_all_by("ip_subnets", {"client_id": client_id})
    peer = db.find_one("wireguard_peers", {"client_id": client_id})
    email_log = db.find_all_by("email_log", {"client_id": client_id})
    pools = db.find_all("ip_pools")
    
    client_details = {"ips": [], "subnets": [], "peer": peer, "email_log": email_log}
    for ip in ips:
        pool = db.find_one("ip_pools", {"id": ip["pool_id"]})
        client_details["ips"].append({**ip, "pool_name": pool.get("name", "N/A")})
    for sub in subnets:
        pool = db.find_one("ip_pools", {"id": sub["pool_id"]})
        client_details["subnets"].append({**sub, "pool_name": pool.get("name", "N/A")})
        
    return templates.TemplateResponse("client_detail.html", {
        "request": request,
        "client": client,
        "client_details": client_details,
        "pools": pools
    })

@app.post("/client/{client_id}/delete")
async def delete_client_web(client_id: int, db: BIC_DB = Depends(get_db)):
    # This is now handled by the generic action endpoint
    # This can be removed if we update the client detail page to use the action endpoint
    from bic.modules import client_management # Avoid circular import issues
    client_management.deprovision_and_delete_client(db, client_id)
    return RedirectResponse(url="/clients", status_code=303)

@app.post("/client/{client_id}/toggle-smtp")
async def toggle_smtp_web(client_id: int, db: BIC_DB = Depends(get_db)):
    # WARNING: Firewall synchronization requires sudo. See note above.
    client = db.find_one("clients", {"id": client_id})
    new_status = not client["allow_smtp"]
    db.update("clients", client_id, {"allow_smtp": int(new_status)})
    # from bic.modules import firewall_management
    # firewall_management.synchronize_firewall_rules(db)
    return RedirectResponse(url=f"/client/{client_id}", status_code=303)

@app.post("/client/{client_id}/add-subnet")
async def add_subnet_web(client_id: int, request: Request, db: BIC_DB = Depends(get_db)):
    # WARNING: This should trigger a WireGuard update, which requires sudo. See note above.
    from bic.modules import network_management # Avoid circular import issues
    form_data = await request.form()
    pool_id = int(form_data.get('pool_id'))
    prefix_len = int(form_data.get('prefix_len'))
    
    subnet_str, subnet_id = network_management.find_and_allocate_subnet(db, pool_id, prefix_len)
    if subnet_str:
        db.update('ip_subnets', subnet_id, {'client_id': client_id})
        # wireguard_management.update_wg_config_for_client(db, client_id)

    return RedirectResponse(url=f"/client/{client_id}", status_code=303)


# --- API Endpoints ---
@app.get("/api/stats")
async def get_stats_api(db: BIC_DB = Depends(get_db)):
    return statistics_management.gather_all_statistics(db)


# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("webapp:app", host="127.0.0.1", port=8000, reload=True)
