import os
import sys
from pathlib import Path

# --- Core Workspace Directory Mappings ---
ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
FLATTENED_DIR = WORKSPACE_DIR / "flattened"  # Added back for Path 1 profile staging
OUTPUT_DIR = ROOT_DIR / "Output"
GCODE_DIR = OUTPUT_DIR / "Gcode"

def ensure_directories():
    """Guarantees the system directory hierarchy is completely built before run execution."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    FLATTENED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GCODE_DIR.mkdir(parents=True, exist_ok=True)

def detect_orca_slicer_path() -> str:
    """Queries standard fallback installation routes across environment spaces to locate OrcaSlicer."""
    standard_routes = [
        Path("C:/Program Files/OrcaSlicer/orca-slicer.exe"),
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\OrcaSlicer\orca-slicer.exe")),
        Path("C:/Program Files (x86)/OrcaSlicer/orca-slicer.exe")
    ]
    for route in standard_routes:
        if route.exists():
            return str(route)
    return ""

def get_orca_roaming_paths():
    """Resolves active local directory hooks into the system roaming database folder profiles."""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return None, None, None
        
    base_orca_roaming = Path(appdata) / "OrcaSlicer"
    printers_dir = base_orca_roaming / "user" / "default" / "machine"
    system_dir = base_orca_roaming / "system"
    user_dir = base_orca_roaming / "user" / "default"
    
    return printers_dir, system_dir, user_dir