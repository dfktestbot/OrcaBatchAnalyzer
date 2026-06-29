import sys
import subprocess
from pathlib import Path
from typing import List
import config

def run_flattening_pipeline(printer_path: Path, process_path: Path, filament_path: Path) -> List[Path]:
    """
    Takes individual configuration profiles and routes them through the fully
    intact vendored orcaslicer-filament-tool directory via its native execution path.
    """
    # Point directly to the root of the full vendored tool directory
    vendor_tool_root = Path(__file__).resolve().parent.parent / "vendor" / "orcaslicer-filament-tool"
    
    if not vendor_tool_root.exists():
        raise FileNotFoundError(
            f"Vendored tool missing. Please ensure the complete folder is copied to: {vendor_tool_root}"
        )

    profiles_to_flatten = [printer_path, process_path, filament_path]
    flattened_outputs = []
    
    for profile in profiles_to_flatten:
        output_name = profile.stem + ".flattened.json"
        output_file = config.FLATTENED_DIR / output_name
        
        print(f" -> Packaging profile via vendor: {profile.name}")
        
        # This matches your old baseline execution strategy 1:1.
        # By setting cwd=vendor_tool_root, 'src.cli' resolves its native paths perfectly.
        subprocess.run([
            sys.executable, 
            "-m", "src.cli", 
            "export", str(profile), 
            "-o", str(config.FLATTENED_DIR)
        ], cwd=str(vendor_tool_root), check=True)
            
        flattened_outputs.append(output_file)
        
    return flattened_outputs