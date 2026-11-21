import sys
import gc  # Imported for core memory cleaning optimization routines
import multiprocessing
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import config
from core.bundle import OrcaProfileManager
from core.flatten import run_flattening_pipeline
from core.slicer import OrcaSlicerEngine
from core.parser import GCodeAnalyticParser
from core.report import ProductionReporter


def execute_analysis_workflow(ui, settings):
    """Runs in a worker thread. Uses `settings` (a snapshot) and the thread-safe `ui` helpers only."""
    is_perf_optimized = settings.performance_mode

    try:
        if is_perf_optimized:
            ui.log("\n[PERFORMANCE MODE ENGAGED]", override_perf=True)
            ui.log("-> Live UI console logs suspended.\n-> Progress tracking isolated to the stationary status bar.", override_perf=True)
        else:
            ui.log("\n====== Starting Slicing & Extraction Loop ======")

        config.ensure_directories()

        orca_exe = Path(settings.orca_exe)
        input_target = Path(settings.input_path)
        strategy_mode = settings.quantity_mode
        flat_fallback = settings.flat_quantity
        source_input_str = settings.input_path

        if input_target.is_file():
            if input_target.suffix.lower() == '.stl':
                stl_models = [input_target]
                input_root_dir = input_target.parent
            else:
                ui.log("[!] Target file is not an STL file format.", override_perf=True)
                ui.show_error("Invalid File", "The selected item is not a valid .stl file layout.")
                return
        else:
            stl_models = sorted(input_target.rglob("*.stl"))
            input_root_dir = input_target

        if not stl_models:
            ui.log(f"[!] Target empty: No STL files located at: {input_target}", override_perf=True)
            ui.show_warning("No Models Found", "No .stl models were discovered in the target input selection.")
            return

        total_files = len(stl_models)
        ui.log(f"[✓] Discovered target slice models: {total_files}", override_perf=True)
        ui.update_progress(0, total_files, "Starting Up...")

        reporter = ProductionReporter()
        manifest_map = {}
        if strategy_mode == "Per-Model Manifest File":
            manifest_map = reporter._load_manifest_quantities(Path(source_input_str))
            if not manifest_map:
                ui.log("[!] Manifest mode selected but no usable entries were found in quantities.txt "
                       "(file missing or empty). Every model will use quantity 1.", override_perf=True)
            else:
                known = {m.name.lower() for m in stl_models}
                for unmatched in sorted(set(manifest_map) - known):
                    ui.log(f"[!] quantities.txt lists '{unmatched}' but no STL with that name was found.", override_perf=True)

        _, _, user_dir = config.get_orca_roaming_paths()
        bundle_manager = OrcaProfileManager()
        p_file, pr_file, f_file = bundle_manager.locate_profile_paths(
            user_dir, settings.printer_profile, settings.process_profile, settings.filament_profile
        )

        ui.log("Executing background profile flattening configurations...", override_perf=True)
        flat_printer, flat_process, flat_filament = run_flattening_pipeline(p_file, pr_file, f_file)

        slicer_engine = OrcaSlicerEngine(orca_exe)
        stats_parser = GCodeAnalyticParser()
        analysis_results = []

        for idx, model in enumerate(stl_models, start=1):
            ui.update_progress(idx - 1, total_files, f"Slicing: {model.name}")
            ui.log(f"Processing Matrix Slice Target: {model.name}")

            try:
                gcode_path = slicer_engine.slice_stl(model, flat_printer, flat_process, flat_filament, input_root_dir)
                metrics = stats_parser.process_gcode_file(gcode_path, model, input_root_dir)
                analysis_results.append(metrics)
                if metrics["status"] == "success":
                    ui.log(f" -> Completed: {metrics['print_time']} | {metrics['filament_g']}g")
                else:
                    ui.log(f" [!] {model.name}: {metrics['error']}", override_perf=True)
            except Exception as inner_err:
                ui.log(f" [!] Slicing conversion failed on asset {model.name}: {inner_err}", override_perf=True)
                analysis_results.append({
                    "model": model.name, "relative_path": str(model.relative_to(input_root_dir)),
                    "print_time": "", "print_time_seconds": 0, "filament_mm": "", "filament_cm3": "",
                    "filament_g": "", "filament_cost": "", "gcode_path": "", "status": "failed", "error": str(inner_err)
                })

            if is_perf_optimized:
                gc.collect()

        ui.update_progress(total_files, total_files, "Compiling CSV Output...")
        csv_out = reporter.write_csv_output(
            analysis_results,
            input_path_str=source_input_str,
            mode=strategy_mode,
            fallback_flat_qty=flat_fallback
        )

        final_qty = 0
        final_secs = 0
        final_grams = 0.0
        failed_count = 0
        SETUP_OVERHEAD_SECS = 300  # must match core/report.py

        for r in analysis_results:
            if r.get("status") == "success":
                m_qty = manifest_map.get(r["model"].lower(), flat_fallback) if strategy_mode == "Per-Model Manifest File" else flat_fallback
                final_qty += m_qty
                final_secs += (int(r.get("print_time_seconds", 0)) + SETUP_OVERHEAD_SECS) * m_qty
                final_grams += reporter.safely_cast_float(r.get("filament_g", 0.0)) * m_qty
            else:
                failed_count += 1

        ui.log("\n====== Run Execution Completed ======", override_perf=True)
        ui.log(f"[✓] Analysis sheet written to: {csv_out}", override_perf=True)
        ui.update_progress(total_files, total_files, "Completed Successfully!" if not failed_count else f"Completed with {failed_count} failure(s)")

        failure_note = (f"\n⚠ {failed_count} model(s) failed - see the status column in results.csv "
                        f"and the log:\n{config.LOG_DIR / 'app.log'}\n") if failed_count else ""
        success_message = (
            f"Batch Analysis Completed{' with errors' if failed_count else ' Successfully'}!\n\n"
            f"Models Sliced Successfully: {total_files - failed_count} of {total_files}\n"
            f"Total Calculated Run Copies: {final_qty}\n"
            f"Total Production Time (With Setup): {reporter.format_seconds(final_secs)}\n"
            f"Total Filament Usage: {final_grams:.1f} g\n"
            f"{failure_note}\n"
            f"Results sheet saved to:\n{csv_out}"
        )
        ui.show_info("Batch Complete", success_message)

    except Exception as fatal_pipeline_error:
        ui.log(f"\n[!] Pipeline Processing Interrupted: {fatal_pipeline_error}", override_perf=True)
        ui.update_progress(0, 100, "Error Occurred")
        ui.show_error("Pipeline Error", f"A fatal error halted processing:\n{fatal_pipeline_error}")

    finally:
        ui.set_running(False)
        gc.collect()


def run_selftest(out_file: str) -> int:
    """
    Non-GUI health check used by CI against the built exe: `OrcaBatchAnalyzer.exe --selftest result.txt`.
    Writes a report to out_file (a windowed exe has no console) and returns an exit code.
    """
    import importlib.util
    lines, ok = [], True

    def check(name, passed, detail=""):
        nonlocal ok
        ok = ok and passed
        lines.append(f"{'PASS' if passed else 'FAIL'}  {name} {detail}".rstrip())

    check("frozen build", True, f"(frozen={config.FROZEN})")
    try:
        import tkinter  # noqa: F401
        check("tkinter available", True)
    except Exception as exc:
        check("tkinter available", False, str(exc))
    vendor = config.BUNDLE_DIR / "vendor" / "orcaslicer-filament-tool"
    check("vendored tool present", vendor.is_dir() and any(vendor.iterdir()), str(vendor))
    try:
        sys.path.insert(0, str(vendor))
        spec = importlib.util.find_spec("src.cli")
        # runpy (used to launch the tool in-process) needs the loader to hand back the module's code
        check("vendored src.cli importable", spec is not None and spec.loader.get_code("src.cli") is not None)
    except Exception as exc:
        check("vendored src.cli importable", False, str(exc))
    try:
        config.ensure_directories()
        probe = config.WORKSPACE_DIR / ".write_test"
        probe.write_text("ok")
        probe.unlink()
        check("data folder writable", True, str(config.DATA_DIR))
    except Exception as exc:
        check("data folder writable", False, str(exc))

    Path(out_file).write_text("\n".join(lines) + f"\n\nRESULT: {'OK' if ok else 'FAILED'}\n", encoding="utf-8")
    return 0 if ok else 1


def main():
    multiprocessing.freeze_support()

    if "--selftest" in sys.argv:
        idx = sys.argv.index("--selftest")
        out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "selftest.txt"
        sys.exit(run_selftest(out))

    log_file = config.setup_logging()
    from gui import AnalyzerGUI  # imported late so --selftest works without a display
    app = AnalyzerGUI(run_pipeline_callback=execute_analysis_workflow)
    app.log(f"Log file: {log_file}", override_perf=True)
    app.mainloop()


if __name__ == "__main__":
    main()
