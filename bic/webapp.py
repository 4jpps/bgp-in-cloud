#!/usr/bin/env python
"""
This is the main FastAPI web application file.

It defines all the routes, middleware, and application logic for the web UI.
"""

import inspect
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt

from bic.core import BIC_DB, get_logger, SECRET_KEY, ALGORITHM
from bic.ui.main import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction
from bic.modules import (
    system_management,
    statistics_management,
    update_management,
    user_management,
    wireguard_management,
    passkey_management,
    yubikey_management,
    google_authenticator_management,
)
from bic.__version__ import __version__

RP_ID = os.getenv("RP_ID", "localhost")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/action/auth/login")

# --- Background Tasks & Lifespan ---

async def periodic_update_check(app_state):
    """Periodically checks for updates and stores the result in app state."""
    while True:
        log.info("Performing periodic background check for updates.")
        try:
            update_available, latest_version = await asyncio.to_thread(update_management.is_update_available)
            app_state.update_available = update_available
            app_state.latest_version = latest_version
        except Exception as e:
            log.error(f"Failed to perform background update check: {e}", exc_info=True)
        await asyncio.sleep(3600)  # Check once per hour

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    app.state.update_available = False
    app.state.latest_version = None
    task = asyncio.create_task(periodic_update_check(app.state))
    yield
    task.cancel()

# --- App Setup ---
log = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="BGP in Cloud IPAM", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BASE_DIR = Path(__file__).resolve().parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "templates"))
templates.env.globals['datetime'] = datetime
templates.env.globals['__version__'] = __version__

# --- DB Dependency ---
def get_db():
    """FastAPI dependency to get a DB instance for a request."""
    db = BIC_DB(base_dir=str(BASE_DIR.parent))
    try:
        yield db
    finally:
        pass

# --- Authentication ---
async def get_current_user(request: Request, db: BIC_DB = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/page/auth/login")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        # Redirect to login on token error
        response = RedirectResponse(url="/page/auth/login", status_code=302)
        response.delete_cookie(key="access_token")
        return response

    user = await asyncio.to_thread(db.find_one, "users", {"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

async def get_current_user_optional(request: Request, db: BIC_DB = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = await asyncio.to_thread(db.find_one, "users", {"username": username})
        return user
    except JWTError:
        return None

# --- UI Navigation Helper ---
def find_ui_item_by_path(request_path: str, request: Request, menu: UIMenu = menu_structure, parent_role: str = None) -> UIMenuItem | None:
    """Recursively searches the menu structure for an item that matches the request path."""
    for item in menu.items:
        # The role for the current level is inherited from the parent, or defined on the menu itself.
        level_role = parent_role or getattr(menu, 'required_role', None)
        
        # The item's own explicit role overrides the inherited one.
        item_role = item.required_role or level_role
        
        # The role of the content (the actual view/menu) is the most specific.
        content_role = getattr(item.item, 'required_role', None)
        
        # The effective role is the most specific one found.
        effective_role = content_role or item_role
        
        # Assign it for the check in render_page.
        # This modification is temporary for the request.
        item.required_role = effective_role

        # Check for exact match first
        if item.path == request_path:
            return item

        # Check for match with path parameters (e.g., /edit/{id})
        path_parts = item.path.split('/')
        request_parts = request_path.split('/')

        if len(path_parts) == len(request_parts):
            match = True
            params = {}
            for p_part, r_part in zip(path_parts, request_parts):
                if p_part.startswith('{') and p_part.endswith('}'):
                    param_name = p_part.strip('{}')
                    params[param_name] = r_part
                elif p_part != r_part:
                    match = False
                    break
            if match:
                if not hasattr(request, 'state'):
                    request.state = lambda: None
                request.state.path_params = params
                return item

        # Recurse into submenus
        if isinstance(item.item, UIMenu) and request_path.startswith(item.path + "/"):
            sub_path = request_path.split(item.path + '/', 1)[1]
            found = find_ui_item_by_path(sub_path, request, item.item, effective_role)
            if found:
                return found

    return None

# --- Core Routes ---

async def get_base_context(request: Request, db: BIC_DB, user: dict | None) -> dict:
    logo_exists = (BASE_DIR.parent / "static" / "assets" / "logo.png").exists()
    return {
        "request": request,
        "menu": menu_structure,
        "settings": system_management.get_all_settings(db),
        "update_available": request.app.state.update_available,
        "latest_version": request.app.state.latest_version,
        "current_user": user,
        "logo_exists": logo_exists,
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: BIC_DB = Depends(get_db), user: dict = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    context = await get_base_context(request, db, user)
    context["stats"] = statistics_management.gather_all_statistics(db)
    return templates.TemplateResponse(request, "dashboard.html", context)

@app.get("/page/{path:path}", response_class=HTMLResponse)
async def render_page(request: Request, path: str, db: BIC_DB = Depends(get_db), user: dict = Depends(get_current_user_optional)):
    if not user and path != 'auth/login':
        return RedirectResponse(url="/page/auth/login")

    item_container = find_ui_item_by_path(path, request)
    if not item_container:
        raise HTTPException(status_code=404, detail="Page not found")

    if item_container.required_role and (not user or user['role'] != item_container.required_role):
        raise HTTPException(status_code=403, detail="Forbidden")

    item = item_container.item

    context = await get_base_context(request, db, user)
    context["item"] = item

    if isinstance(item, UIMenu):
        return templates.TemplateResponse(request, "generic_menu.html", context)
    
    if isinstance(item, UIView):
        if item.loader:
            path_params = request.state.path_params if hasattr(request.state, 'path_params') else {}
            loader_data = await asyncio.to_thread(item.loader, db_core=db, **path_params)
            context["data"] = loader_data
            context["peer"] = loader_data

        if item.handler:
            path_params = request.state.path_params if hasattr(request.state, 'path_params') else {}
            query_params = request.query_params
            handler_kwargs = {**path_params, **dict(query_params), "db_core": db}
            context['list_data'] = await asyncio.to_thread(item.handler, **handler_kwargs)
        return templates.TemplateResponse(request, item.template, context)

    if isinstance(item, UIAction):
        for field in item.form_fields:
            if field.options_loader:
                field.options = await asyncio.to_thread(field.options_loader, db_core=db)
        if item.loader:
            path_params = request.state.path_params if hasattr(request.state, 'path_params') else {}
            loader_data = await asyncio.to_thread(item.loader, db_core=db, **path_params)
            context["data"] = loader_data
        return templates.TemplateResponse(request, item.template, context)

    raise HTTPException(status_code=404, detail="Path does not lead to a renderable page")

@app.post("/action/auth/login")
@limiter.limit("5/minute")
async def handle_login(request: Request, db: BIC_DB = Depends(get_db)):
    form_data = await request.form()
    user = await asyncio.to_thread(user_management.login_user, db_core=db, username=form_data['username'], password=form_data['password'])
    if not user or not isinstance(user, dict):
        return RedirectResponse(url="/page/auth/login?error=1", status_code=303)

    yubikey = await asyncio.to_thread(db.find_one, "yubikey_credentials", {"user_id": user['id']})
    google_auth = await asyncio.to_thread(db.find_one, "google_authenticator_secrets", {"user_id": user['id']})

    if yubikey or google_auth:
        # Store the user in the session and redirect to the 2FA page
        request.session['2fa_user_id'] = user['id']
        return RedirectResponse(url="/page/auth/2fa", status_code=303)

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=user["access_token"], httponly=True)
    return response

@app.post("/action/{path:path}")
async def handle_action(request: Request, path: str, db: BIC_DB = Depends(get_db)):
    current_user = await get_current_user(request, db)
    if isinstance(current_user, RedirectResponse):
        return current_user

    item_container = find_ui_item_by_path(path, request)
    if not item_container or not isinstance(item_container.item, UIAction):
        raise HTTPException(status_code=404, detail="Action not found")

    if item_container.required_role and (not current_user or current_user['role'] != item_container.required_role):
        raise HTTPException(status_code=403, detail="Forbidden")

    item = item_container.item

    form_data = await request.form()
    path_params = request.state.path_params if hasattr(request.state, 'path_params') else {}
    form_dict = {**path_params, **{k: v for k, v in form_data.items()}}
    log.info(f"Handling action '{path}' with combined data: {form_dict}")

    # Handle file uploads
    for key, value in form_data.items():
        if isinstance(value, UploadFile):
            if key == 'branding_logo':
                # Ensure the assets directory exists
                assets_dir = BASE_DIR.parent / "static" / "assets"
                assets_dir.mkdir(exist_ok=True)
                file_path = assets_dir / "logo.png"
                with open(file_path, "wb") as buffer:
                    buffer.write(await value.read())
                log.info(f"Saved uploaded logo to {file_path}")
                # We don't pass the file content to the handler
                form_dict.pop(key, None)

    try:
        handler_params = inspect.signature(item.handler).parameters
        if 'user' in handler_params:
            form_dict['user'] = current_user

        result = await asyncio.to_thread(item.handler, db_core=db, **form_dict)
        user_management.add_audit_log(db, user_id=current_user['id'], action=f"execute_action:{path}", details=str(form_dict))

        if isinstance(result, dict):
            return JSONResponse(content=result)

    except Exception as e:
        log.error(f"Error executing action handler for '{path}': {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

    redirect_path = item.redirect_to or request.headers.get("referer", "/")
    if "{id}" in redirect_path:
        redirect_path = redirect_path.format(id=path_params.get('id') or form_dict.get('id'))
    if "{peer_id}" in redirect_path:
        redirect_path = redirect_path.format(peer_id=path_params.get('peer_id') or form_dict.get('peer_id'))
    return RedirectResponse(url=redirect_path, status_code=303)

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/page/auth/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get("/download/wireguard/client/{client_id}")
async def download_wg_config(client_id: str, db: BIC_DB = Depends(get_db)):
    config = await asyncio.to_thread(wireguard_management.get_client_wireguard_config, db_core=db, client_id=client_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found.")

    return Response(
        content=config['content'],
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={config['filename']}"
        }
    )

# --- API Routes & WebSocket ---

@app.get("/api/check-update", response_class=JSONResponse)
async def check_update_api(request: Request):
    update_available, latest_version = await asyncio.to_thread(update_management.is_update_available)
    request.app.state.update_available = update_available
    request.app.state.latest_version = latest_version
    return {"update_available": update_available, "latest_version": latest_version}

@app.post("/api/perform-update", response_class=JSONResponse)
async def perform_update_api():
    result = await asyncio.to_thread(update_management.perform_update)
    return result

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    log_file = BASE_DIR.parent / "bic.log"
    if not log_file.exists():
        await websocket.send_text("Log file not found.")
        await websocket.close()
        return

    try:
        with open(log_file, "r") as f:
            f.seek(0, 2)
            pos = f.tell()
            lines = []
            while pos > 0 and len(lines) < 20:
                pos -= 1
                f.seek(pos, 0)
                if f.read(1) == '\n':
                    lines.append(f.readline())
            await websocket.send_text("\n".join(reversed(lines)))

            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                await websocket.send_json({'type': 'log', 'payload': line})
    except WebSocketDisconnect:
        log.info("Log WebSocket client disconnected.")
    except Exception as e:
        log.error(f"Error in log WebSocket: {e}")
    finally:
        if not websocket.client_state == "DISCONNECTED":
            await websocket.close()

# --- Passkey (WebAuthn) Routes ---

@app.get("/api/passkey/register/options/{user_id}", response_class=JSONResponse)
async def passkey_register_options(user_id: str, db: BIC_DB = Depends(get_db)):
    user = await asyncio.to_thread(user_management.get_user, db_core=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    options = await asyncio.to_thread(passkey_management.get_registration_options, db_core=db, user_id=user_id, username=user['username'])
    return options.dict()

@app.post("/api/passkey/register/verify/{user_id}")
async def passkey_register_verify(user_id: str, request: Request, db: BIC_DB = Depends(get_db)):
    credential = await request.json()
    await asyncio.to_thread(passkey_management.verify_registration, db_core=db, user_id=user_id, credential=credential)
    return {"success": True}

@app.get("/api/passkey/auth/options/{username}", response_class=JSONResponse)
async def passkey_auth_options(username: str, db: BIC_DB = Depends(get_db)):
    user = await asyncio.to_thread(db.find_one, "users", {"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    options = await asyncio.to_thread(passkey_management.get_authentication_options, db_core=db, user_id=user['id'])
    return options.dict()

@app.post("/api/passkey/auth/verify/{username}")
async def passkey_auth_verify(username: str, request: Request, db: BIC_DB = Depends(get_db)):
    credential = await request.json()
    user = await asyncio.to_thread(db.find_one, "users", {"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await asyncio.to_thread(passkey_management.verify_authentication, db_core=db, user_id=user['id'], credential=credential)
    
    # Create a session for the user
    access_token = user_management.create_access_token(data={"sub": user['username']})
    response = JSONResponse(content={"success": True})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# --- YubiKey Routes ---

@app.post("/api/yubikey/associate/{user_id}")
async def yubikey_associate(user_id: str, request: Request, db: BIC_DB = Depends(get_db)):
    data = await request.json()
    otp = data.get("otp")
    if not otp:
        raise HTTPException(status_code=400, detail="OTP is required")

    success = await asyncio.to_thread(yubikey_management.associate_yubikey, db_core=db, user_id=user_id, otp=otp)
    return {"success": success}

# --- Google Authenticator Routes ---

@app.get("/api/google-authenticator/generate-secret/{user_id}")
async def google_authenticator_generate_secret(user_id: str, db: BIC_DB = Depends(get_db)):
    user = await asyncio.to_thread(db.find_one, "users", {"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret_data = await asyncio.to_thread(google_authenticator_management.generate_secret, db_core=db, user_id=user_id, username=user['username'])
    return {"success": True, **secret_data}


@app.post("/action/auth/2fa")
async def handle_2fa(request: Request, db: BIC_DB = Depends(get_db)):
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return RedirectResponse(url="/page/auth/login?error=2", status_code=303)  # Session expired

    form_data = await request.form()
    otp = form_data.get("otp")
    if not otp:
        return RedirectResponse(url="/page/auth/2fa?error=1", status_code=303)  # OTP is required

    # Try to verify with any available 2FA method
    yubikey_valid = await asyncio.to_thread(yubikey_management.verify_yubikey, db_core=db, user_id=user_id, otp=otp)

    google_auth_valid = False
    if not yubikey_valid:
        google_auth_valid = await asyncio.to_thread(google_authenticator_management.verify_otp, db_core=db, user_id=user_id, otp=otp)

    if not (yubikey_valid or google_auth_valid):
        return RedirectResponse(url="/page/auth/2fa?error=1", status_code=303)  # Invalid OTP

    # If successful, create a session for the user
    user = await asyncio.to_thread(db.find_one, "users", {"id": user_id})
    access_token = user_management.create_access_token(data={"sub": user['username']})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    del request.session['2fa_user_id']  # Clean up the session
    return response




