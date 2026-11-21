import logging
import os
import shutil
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_NAME = "OrcaBatchAnalyzer"
FROZEN = bool(getattr(sys, "frozen", False))

# --- Where bundled (read-only) files live vs. where we may write ---
if FROZEN:
    # PyInstaller: bundled files are unpacked next to the exe (or in _MEIPASS).
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    # Never write next to the exe: it may sit in Program Files or a read-only folder.
    DATA_DIR = Path(os.getenv("LOCALAPPDATA") or Path.home()) / APP_NAME
    DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / APP_NAME / "Output"
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BUNDLE_DIR
    DEFAULT_OUTPUT_DIR = BUNDLE_DIR / "Output"

ROOT_DIR = BUNDLE_DIR  # kept for backwards compatibility
WORKSPACE_DIR = DATA_DIR / "workspace"
FLATTENED_DIR = WORKSPACE_DIR / "flattened"  # staging area for flattened profiles
LOG_DIR = DATA_DIR / "logs"
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
GCODE_DIR = OUTPUT_DIR / "Gcode"


def ensure_directories():
    """Guarantees the system directory hierarchy is completely built before run execution."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    FLATTENED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GCODE_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> Path:
    """Log to a file so problems are diagnosable even in a windowed exe (no console)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "app.log"
    logger = logging.getLogger(APP_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return log_file


def detect_orca_slicer_path() -> str:
    """Queries standard installation routes to locate OrcaSlicer."""
    candidates = []
    for env_var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        base = os.getenv(env_var)
        if base:
            candidates.append(Path(base) / "OrcaSlicer" / "orca-slicer.exe")
    local = os.getenv("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Programs" / "OrcaSlicer" / "orca-slicer.exe")
    candidates += [
        Path("C:/Program Files/OrcaSlicer/orca-slicer.exe"),
        Path("C:/Program Files (x86)/OrcaSlicer/orca-slicer.exe"),
    ]
    for route in candidates:
        if route.exists():
            return str(route)
    on_path = shutil.which("orca-slicer")
    return on_path or ""


def get_orca_roaming_paths():
    """Resolves OrcaSlicer's roaming profile folders. Returns (printers_dir, system_dir, user_dir)."""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return None, None, None

    base_orca_roaming = Path(appdata) / "OrcaSlicer"
    system_dir = base_orca_roaming / "system"
    users_root = base_orca_roaming / "user"

    def has_profiles(p: Path) -> bool:
        return any((p / sub).is_dir() and any((p / sub).glob("*.json")) for sub in ("machine", "process", "filament"))

    # OrcaSlicer uses user/default when signed out, but a numeric user-id folder when signed in.
    user_dir = users_root / "default"
    if not has_profiles(user_dir) and users_root.is_dir():
        for candidate in sorted(users_root.iterdir()):
            if candidate.is_dir() and has_profiles(candidate):
                user_dir = candidate
                break

    printers_dir = user_dir / "machine"
    return printers_dir, system_dir, user_dir
