import subprocess
from pathlib import Path
import config

class OrcaSlicerEngine:
    """Manages orchestration of background slicing tasks via OrcaSlicer native CLI using flattened JSON profiles."""
    
    def __init__(self, executable_path: Path):
        self.exe_path = executable_path
        if not self.exe_path.exists():
            raise FileNotFoundError(f"OrcaSlicer execution engine path not valid: {self.exe_path}")

    @staticmethod
    def clean_filename(name: str) -> str:
        """Converts erratic or unsafe string naming options cleanly into standardized system syntax."""
        invalid = '<>:"/\\|?*'
        cleaned = "".join("_" if c in invalid else c for c in name)
        return cleaned.strip() or "model"

    def slice_stl(self, model_path: Path, flattened_printer: Path, flattened_process: Path, flattened_filament: Path) -> Path:
        """Executes a blocking subprocess call to slice an STL using paths to validated flattened profiles."""
        safe_name = self.clean_filename(model_path.stem)
        model_output_dir = config.GCODE_DIR / safe_name
        
        if model_output_dir.exists():
            import shutil
            shutil.rmtree(model_output_dir)
        model_output_dir.mkdir(parents=True, exist_ok=True)

        # Build command using OrcaSlicer's validated file-loading interface
        # printer and process presets must be semi-colon separated under --load-settings
        command = [
            str(self.exe_path),
            "--slice", "0",
            "--orient", "1",
            "--load-settings", f"{flattened_printer};{flattened_process}",
            "--load-filaments", str(flattened_filament),
            "--allow-newer-file",
            "--outputdir", str(model_output_dir),
            str(model_path)
        ]

        # Execute the slicing runner cleanly
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # If the slicing engine failed, dump the logs directly to the terminal window
        if result.returncode != 0:
            print("\n====== ORCA SLICER CLI ERROR LOG ======")
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)
            print("========================================\n")

        output_gcode = model_output_dir / "plate_1.gcode"
        if not output_gcode.exists():
            raise FileNotFoundError(f"Slicing complete, but output file missing at: {output_gcode}")

        return output_gcode