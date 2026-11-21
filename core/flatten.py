import contextlib
import io
import logging
import os
import runpy
import subprocess
import sys
from pathlib import Path
from typing import List

import config

log = logging.getLogger(config.APP_NAME)

# Windows: stop a console window flashing up for every child process.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _vendor_root() -> Path:
    return config.BUNDLE_DIR / "vendor" / "orcaslicer-filament-tool"


def _export_in_process(vendor_root: Path, profile: Path, out_dir: Path) -> None:
    """
    Runs the vendored `python -m src.cli export ...` inside this process.

    A packaged (PyInstaller) build has no separate Python interpreter: sys.executable is
    OrcaBatchAnalyzer.exe itself, so launching `sys.executable -m src.cli` would just
    start another copy of this app. Running the module in-process works in both cases.
    """
    old_argv, old_cwd, old_path = sys.argv[:], os.getcwd(), sys.path[:]
    captured = io.StringIO()
    try:
        os.chdir(vendor_root)
        sys.path.insert(0, str(vendor_root))
        sys.argv = ["src.cli", "export", str(profile), "-o", str(out_dir)]
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            try:
                runpy.run_module("src.cli", run_name="__main__", alter_sys=True)
            except SystemExit as exc:
                if exc.code not in (None, 0):
                    raise RuntimeError(f"profile export exited with code {exc.code}") from exc
    except Exception as exc:
        log.error("Profile export failed for %s:\n%s", profile.name, captured.getvalue())
        tail = captured.getvalue().strip()[-500:]
        raise RuntimeError(f"Could not flatten profile '{profile.name}': {exc}\n{tail}") from exc
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv
        sys.path[:] = old_path
        log.info("Export output for %s:\n%s", profile.name, captured.getvalue())


def _export_subprocess(vendor_root: Path, profile: Path, out_dir: Path) -> None:
    """Source-checkout path: run the tool with the current Python interpreter."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "export", str(profile), "-o", str(out_dir)],
        cwd=str(vendor_root),
        capture_output=True,
        text=True,
        creationflags=_NO_WINDOW,
    )
    log.info("Export output for %s:\n%s\n%s", profile.name, result.stdout, result.stderr)
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not flatten profile '{profile.name}' (exit {result.returncode}):\n"
            f"{(result.stderr or result.stdout).strip()[-500:]}"
        )


def run_flattening_pipeline(printer_path: Path, process_path: Path, filament_path: Path) -> List[Path]:
    """
    Takes individual configuration profiles and routes them through the vendored
    orcaslicer-filament-tool so inherited settings are resolved into standalone files.
    """
    vendor_tool_root = _vendor_root()
    if not vendor_tool_root.exists() or not any(vendor_tool_root.iterdir()):
        raise FileNotFoundError(
            f"Vendored tool is missing or empty: {vendor_tool_root}\n"
            "If you cloned the repo, run: git submodule update --init --recursive\n"
            "(GitHub's 'Download ZIP' does not include submodules.)"
        )

    flattened_outputs = []
    for profile in (printer_path, process_path, filament_path):
        output_file = config.FLATTENED_DIR / (profile.stem + ".flattened.json")
        if output_file.exists():
            output_file.unlink()  # never reuse a stale file if the export silently does nothing

        log.info("Packaging profile via vendor: %s", profile.name)
        if config.FROZEN:
            _export_in_process(vendor_tool_root, profile, config.FLATTENED_DIR)
        else:
            _export_subprocess(vendor_tool_root, profile, config.FLATTENED_DIR)

        if not output_file.exists():
            raise FileNotFoundError(f"Profile export finished but did not produce: {output_file}")
        flattened_outputs.append(output_file)

    return flattened_outputs
