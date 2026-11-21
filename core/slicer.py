import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import config

log = logging.getLogger(config.APP_NAME)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SLICE_TIMEOUT_SECS = 30 * 60  # one stuck model must not hang the whole batch


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

    def _output_dir_name(self, model_path: Path, input_root: Optional[Path]) -> str:
        """
        Root-level models keep their plain name. Models in subfolders get the folder
        path prefixed so two files called 'bracket.stl' in different folders don't
        overwrite each other's G-code.
        """
        if input_root is not None:
            try:
                rel = model_path.relative_to(input_root).with_suffix("")
                if len(rel.parts) > 1:
                    return self.clean_filename("__".join(rel.parts))
            except ValueError:
                pass
        return self.clean_filename(model_path.stem)

    def slice_stl(self, model_path: Path, flattened_printer: Path, flattened_process: Path,
                  flattened_filament: Path, input_root: Optional[Path] = None) -> Path:
        """Executes a blocking subprocess call to slice an STL using paths to validated flattened profiles."""
        model_output_dir = config.GCODE_DIR / self._output_dir_name(model_path, input_root)

        if model_output_dir.exists():
            shutil.rmtree(model_output_dir)
        model_output_dir.mkdir(parents=True, exist_ok=True)

        # printer and process presets must be semi-colon separated under --load-settings
        command = [
            str(self.exe_path),
            "--slice", "0",
            "--orient", "1",
            "--load-settings", f"{flattened_printer};{flattened_process}",
            "--load-filaments", str(flattened_filament),
            "--allow-newer-file",
            "--outputdir", str(model_output_dir),
            str(model_path),
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=SLICE_TIMEOUT_SECS,
                creationflags=_NO_WINDOW,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OrcaSlicer did not finish within {SLICE_TIMEOUT_SECS // 60} minutes") from None

        # Keep the full CLI output next to the model's G-code and in the app log.
        (model_output_dir / "slicer.log").write_text(
            f"COMMAND:\n{' '.join(command)}\n\nEXIT CODE: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n",
            encoding="utf-8",
        )

        output_gcode = model_output_dir / "plate_1.gcode"
        if not output_gcode.exists():
            detail = (result.stderr or result.stdout or "").strip()[-400:]
            log.error("Slice failed for %s (exit %s):\n%s\n%s", model_path, result.returncode, result.stdout, result.stderr)
            raise FileNotFoundError(
                f"No G-code produced (OrcaSlicer exit code {result.returncode}). "
                f"{detail or 'No output from OrcaSlicer.'} See {model_output_dir / 'slicer.log'}"
            )
        if result.returncode != 0:
            log.warning("OrcaSlicer exit code %s but G-code exists for %s", result.returncode, model_path)

        return output_gcode
