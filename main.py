import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routes import core, archive, editor, pdf, config, oracle, render, settings, auth, admin, comms, blueprint, groupspace
from logic.auth import auth_service, group_store, register_user_creation_hook, register_user_creation_sync_hook
from logic.comms import comms_manager as _comms_manager
from logic.conversion import gotenberg
from logic.oracle import oracle as neural_oracle
from logic.files import StorageCache, register_mutation_hook, PathSanitizer
from logic.exceptions import AegisError

# Register user creation side-effects (comms folder provisioning).
# Must be at module level so hooks are active before bootstrap_admin() runs in lifespan.
register_user_creation_hook(_comms_manager.create_comms_folders)
register_user_creation_sync_hook(_comms_manager.create_comms_folders_sync)

logger = logging.getLogger("aegis.core")

# Paths exempt from authentication
_AUTH_SKIP_PATHS: frozenset[str] = frozenset({"/login", "/logout"})

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AEGIS_BOOT: Initializing persistent resources
    auth_service.bootstrap_admin()
    # Provision group workspaces for any existing groups missing their folder
    for _group_name in group_store.list_groups_sync():
        group_store.provision_group_dirs_sync(_group_name)
    register_mutation_hook(StorageCache.invalidate)
    await neural_oracle.probe_url()
    yield
    # AEGIS_SHUTDOWN: Graceful connection cleanup
    await gotenberg.shutdown()
    await neural_oracle.shutdown()

# AEGIS_ARCH_v4.1.0: SOLID Architecture Refactor
app = FastAPI(
    title="SC-ARCHIVE",
    description="Space Craft Archive Management System // Aegis Class",
    version="5.9.0",
    lifespan=lifespan
)

# 1. Middleware (order matters: last add_middleware = outermost = runs first)
# auth_middleware is registered first so SessionMiddleware wraps it (runs before it)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Guards all routes. Binds per-user workspace root via ContextVar before dispatch."""
    path = request.url.path
    if path in _AUTH_SKIP_PATHS or path.startswith("/static"):
        return await call_next(request)

    username = request.session.get("username")
    if not username:
        if request.headers.get("HX-Request"):
            return Response(status_code=200, headers={"HX-Redirect": "/login"})
        return RedirectResponse(url="/login", status_code=302)

    try:
        user_root = await auth_service.get_user_root(username)
        PathSanitizer.bind_request_root(user_root)
    except AegisError:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    return await call_next(request)


# SessionMiddleware added last = outermost = populates request.session before auth_middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["AEGIS_SECRET_KEY"],
    session_cookie="aegis_session",
    max_age=86400,        # 24h
    https_only=False,     # LAN HTTP — set True when TLS is active
    same_site="lax",
)

# 2. Centralized Exception Handlers (Aegis Stability Protocol)
@app.exception_handler(AegisError)
async def aegis_error_handler(request: Request, exc: AegisError) -> JSONResponse:
    """Translates domain exceptions to structured HTTP responses with logging."""
    logger.warning("AEGIS_FAULT [%s] %s — %s %s", exc.status_code, exc.detail, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# 3. Static and Template Configuration
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4. Router Convergence (APIRouter Implementation)
# Modular domain distribution as per Aegis Architecture Protocol
app.include_router(auth.router)      # Identity & Session
app.include_router(core.router)      # Dashboard & Telemetry
app.include_router(archive.router)   # File Operations
app.include_router(editor.router)    # Buffer Management
app.include_router(pdf.router)       # Conversion Pipeline
app.include_router(config.router)    # Workspace Config
app.include_router(oracle.router)    # Neural Interface (Aegis Oracle)
app.include_router(render.router)    # Mermaid Render Pipeline
app.include_router(settings.router)  # Operational Parameters
app.include_router(admin.router)     # Admin Panel
app.include_router(comms.router)     # Comms Protocol
app.include_router(blueprint.router)   # Blueprint Archive
app.include_router(groupspace.router)  # Group Shared Workspace

# AEGIS_INIT_READY: Server configuration complete.
# Start via bin/launch.sh to initialize Tailwind and Uvicorn logic.
