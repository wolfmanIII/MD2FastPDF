from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from logic.templates import templates
from routes import core, archive, editor, pdf, config

# AEGIS_ARCH_v3.9.4: Modular Architecture Launch
app = FastAPI(
    title="SC-ARCHIVE", 
    description="Space Craft Archive Management System // Aegis Class",
    version="3.9.4"
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

# AEGIS_INIT_READY: Server configuration complete.
# Start via bin/launch.sh to initialize Tailwind and Uvicorn logic.
