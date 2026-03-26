from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from logic.templates import templates
from routes import core, archive, editor, pdf, config, oracle, render
from logic.conversion import gotenberg
from logic.oracle import oracle as neural_oracle

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AEGIS_BOOT: Initializing persistent resources
    yield
    # AEGIS_SHUTDOWN: Graceful connection cleanup
    await gotenberg.shutdown()
    await neural_oracle.shutdown()

# AEGIS_ARCH_v4.1.0: SOLID Architecture Refactor
app = FastAPI(
    title="SC-ARCHIVE", 
    description="Space Craft Archive Management System // Aegis Class",
    version="4.1.0",
    lifespan=lifespan
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

# AEGIS_INIT_READY: Server configuration complete.
# Start via bin/launch.sh to initialize Tailwind and Uvicorn logic.
