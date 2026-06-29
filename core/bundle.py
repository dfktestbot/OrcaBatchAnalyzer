import json
from pathlib import Path
from typing import Dict, Any, Tuple

class OrcaProfileManager:
    """Manages simple discovery and path mapping of custom user profiles for Path 1."""
    
    def __init__(self):
        # Kept as an in-memory reference, but no longer forced into dropdowns
        self.generic_defaults = {
            "printer": "Standard Safe Default - 220mm Bed",
            "filament": "Standard Safe Default - Generic PLA",
            "process_no_supports": "Standard Safe Default - 0.20mm (No Supports)",
            "process_with_supports": "Standard Safe Default - 0.20mm (With Supports)"
        }

    def get_generic_metadata(self) -> Dict[str, Any]:
        """Provides the application UI dropdown items with clean baseline names."""
        return self.generic_defaults

    def discover_user_profiles(self, user_dir: Path) -> Dict[str, list]:
        """
        Scans OrcaSlicer's user directory to discover custom profiles.
        Returns a clean dictionary of human-readable profile names grouped by type.
        """
        profiles = {"printer": [], "process": [], "filament": []}
        
        # --- REMOVED STATIC DEFAULTS FOR GITHUB PUSH ---
        # We will re-introduce these later once physical template files are created.

        if not user_dir or not user_dir.exists():
            return profiles

        folder_mapping = {
            "machine": "printer",
            "process": "process",
            "filament": "filament"
        }

        for source_folder, profile_type in folder_mapping.items():
            target_path = user_dir / source_folder
            if target_path.exists():
                for file in target_path.glob("*.json"):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        name = data.get("name") or data.get("setting_id") or file.stem
                        profiles[profile_type].append(name)
                    except Exception:
                        continue
                        
        return profiles

    def locate_profile_paths(self, user_dir: Path, printer_name: str, process_name: str, filament_name: str) -> Tuple[Path, Path, Path]:
        """
        Maps chosen human-readable dropdown names back to their absolute JSON file paths
        inside the user's roaming directory.
        """
        printer_path = None
        process_path = None
        filament_path = None

        # Helper lambda to look up user files by tracking their internal "name" properties
        def find_user_file(folder_name: str, chosen_name: str) -> Path:
            if not user_dir or not user_dir.exists():
                return None
            search_path = user_dir / folder_name
            if search_path.exists():
                for file in search_path.glob("*.json"):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if (data.get("name") or data.get("setting_id") or file.stem) == chosen_name:
                            return file
                    except Exception:
                        continue
            return None

        # Resolve paths dynamically against the roaming folder
        printer_path = find_user_file("machine", printer_name)
        process_path = find_user_file("process", process_name)
        filament_path = find_user_file("filament", filament_name)

        # Sanity validation
        for label, path in [("Printer", printer_path), ("Process", process_path), ("Filament", filament_path)]:
            if not path or not path.exists():
                raise FileNotFoundError(f"Could not locate underlying file configuration path for '{label}' profile choice.")

        return printer_path, process_path, filament_path