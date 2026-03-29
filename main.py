import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from routes import core, archive, editor, pdf, config, oracle, render, settings
from logic.conversion import gotenberg
from logic.oracle import oracle as neural_oracle
from logic.files import StorageCache, register_mutation_hook
from logic.exceptions import AegisError

logger = logging.getLogger("aegis.core")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AEGIS_BOOT: Initializing persistent resources
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
    version="5.4.0",
    lifespan=lifespan
)

# 3. Centralized Exception Handlers (Aegis Stability Protocol)
@app.exception_handler(AegisError)
async def aegis_error_handler(request: Request, exc: AegisError) -> JSONResponse:
    """Translates domain exceptions to structured HTTP responses with logging."""
    logger.warning("AEGIS_FAULT [%s] %s — %s %s", exc.status_code, exc.detail, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# 1. Static and Template Configuration
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Router Convergence (APIRouter Implementation)
# Modular domain distribution as per Aegis Architecture Protocol
app.include_router(core.router)      # Dashboard & Telemetry
app.include_router(archive.router)   # File Operations
app.include_router(editor.router)    # Buffer Management
app.include_router(pdf.router)       # Conversion Pipeline
app.include_router(config.router)    # Workspace Config
app.include_router(oracle.router)    # Neural Interface (Aegis Oracle)
app.include_router(render.router)    # Mermaid Render Pipeline
app.include_router(settings.router)  # Operational Parameters

# AEGIS_INIT_READY: Server configuration complete.
# Start via bin/launch.sh to initialize Tailwind and Uvicorn logic.
