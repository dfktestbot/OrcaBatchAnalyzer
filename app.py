import sys
from pathlib import Path
from tkinter import messagebox

# Path safeguard for local routing
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import config
from gui import AnalyzerGUI
from core.bundle import OrcaProfileManager
from core.flatten import run_flattening_pipeline
from core.slicer import OrcaSlicerEngine
from core.parser import GCodeAnalyticParser
from core.report import ProductionReporter

def execute_analysis_workflow(ui: AnalyzerGUI):
    ui.log("\n====== Starting Slicing & Extraction Loop ======")
    config.ensure_directories()
    
    orca_exe = Path(ui.orca_exe_path.get())
    input_target = Path(ui.input_path.get())
    
    if input_target.is_file():
        if input_target.suffix.lower() == '.stl':
            stl_models = [input_target]
            input_root_dir = input_target.parent
        else:
            ui.log("[!] Target file is not an STL file format.")
            messagebox.showerror("Invalid File", "The selected item is not a valid .stl file layout.")
            return
    else:
        stl_models = sorted(input_target.rglob("*.stl"))
        input_root_dir = input_target

    if not stl_models:
        ui.log(f"[!] Target empty: No STL files located at: {input_target}")
        messagebox.showwarning("No Models Found", "No .stl models were discovered in the target input selection.")
        return

    ui.log(f"[✓] Discovered target slice models: {len(stl_models)}")

    try:
        # Load directories via configuration settings
        _, _, user_dir = config.get_orca_roaming_paths()
        
        bundle_manager = OrcaProfileManager()
        
        # Aligned to match the file path mapping signatures in core/bundle.py
        p_file, pr_file, f_file = bundle_manager.locate_profile_paths(
            user_dir, ui.printer_profile.get(), ui.process_profile.get(), ui.filament_profile.get()
        )
        
        ui.log("Executing background profile flattening configurations...")
        flat_printer, flat_process, flat_filament = run_flattening_pipeline(p_file, pr_file, f_file)
        
        slicer_engine = OrcaSlicerEngine(orca_exe)
        stats_parser = GCodeAnalyticParser()
        reporter = ProductionReporter()
        
        analysis_results = []
        
        for model in stl_models:
            ui.log(f"Processing Matrix Slice Target: {model.name}")
            try:
                gcode_path = slicer_engine.slice_stl(model, flat_printer, flat_process, flat_filament)
                metrics = stats_parser.process_gcode_file(gcode_path, model, input_root_dir)
                analysis_results.append(metrics)
                ui.log(f" -> Completed: {metrics['print_time']} | {metrics['filament_g']}g")
            except Exception as inner_err:
                ui.log(f" [!] Slicing conversion failed on asset {model.name}: {inner_err}")
                analysis_results.append({
                    "model": model.name, "relative_path": str(model.relative_to(input_root_dir)),
                    "print_time": "", "print_time_seconds": 0, "filament_mm": "", "filament_cm3": "",
                    "filament_g": "", "filament_cost": "", "gcode_path": "", "status": "failed", "error": str(inner_err)
                })

        csv_out = reporter.write_csv_output(analysis_results)
        summary_row = reporter.generate_summary_row(analysis_results)
        
        ui.log("\n====== Run Execution Completed ======")
        ui.log(f"[✓] Analysis sheet written to: {csv_out}")
        
        success_message = (
            f"Batch Analysis Completed Successfully!\n\n"
            f"Total Models Sliced: {len(analysis_results)}\n"
            f"Total Production Time: {summary_row['print_time']}\n"
            f"Total Filament Usage: {summary_row['filament_g']} g\n\n"
            f"Results sheet saved to:\n{csv_out}"
        )
        messagebox.showinfo("Batch Complete", success_message)
        
    except Exception as fatal_pipeline_error:
        ui.log(f"\n[!] Pipeline Processing Interrupted: {fatal_pipeline_error}")
        messagebox.showerror("Pipeline Error", f"A fatal error halted processing:\n{fatal_pipeline_error}")

def main():
    app = AnalyzerGUI(run_pipeline_callback=execute_analysis_workflow)
    app.mainloop()

if __name__ == "__main__":
    main()