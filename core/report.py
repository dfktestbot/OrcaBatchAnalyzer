import csv
from pathlib import Path
import config

class ProductionReporter:
    def __init__(self):
        pass

    def safely_cast_float(self, value) -> float:
        try:
            return float(value) if value not in (None, "") else 0.0
        except ValueError:
            return 0.0

    def format_seconds(self, total_seconds: int) -> str:
        if total_seconds <= 0:
            return "0m 0s"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"

    def _load_manifest_quantities(self, folder_path: Path) -> dict:
        """Looks for a local quantities.txt file inside the specified directory."""
        manifest = {}
        manifest_file = folder_path / "quantities.txt"
        if not manifest_file.exists():
            return manifest
            
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "," in line:
                        parts = line.strip().split(",")
                        if len(parts) >= 2:
                            filename = parts[0].strip().lower()
                            try:
                                qty = int(parts[1].strip())
                                manifest[filename] = qty
                            except ValueError:
                                pass
        except Exception:
            pass
        return manifest

    def write_csv_output(self, results: list, input_path_str: str, mode: str, fallback_flat_qty: int) -> str:
        """
        Compiles the production tracking spreadsheet with selective subfolders subtotals.
        Root-level files are listed individually without generating an artificial subtotal group.
        """
        output_file = config.OUTPUT_DIR / "results.csv"
        ENDER3_OVERHEAD_SECS = 300
        
        input_root = Path(input_path_str)
        manifest_map = {}
        if mode == "Per-Model Manifest File" and input_root.is_dir():
            manifest_map = self._load_manifest_quantities(input_root)

        headers = [
            "Model Name", "Qty", "Slicer Print Time", 
            "Machine Setup Constant", "Total Unit Time", 
            "Scaled Total Time", "Total Filament (g)", "status"
        ]

        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            # Global trackers
            global_qty = 0
            global_slicer_secs = 0
            global_setup_secs = 0
            global_total_secs = 0
            global_grams = 0.0
            global_passed = 0
            global_failed = 0

            # Subtotal trackers for active subdirectories
            current_folder_name = None
            sub_qty = 0
            sub_slicer_secs = 0
            sub_setup_secs = 0
            sub_total_secs = 0
            sub_grams = 0.0
            sub_passed = 0
            sub_failed = 0

            def write_subtotal_row():
                """Writes out accumulated metrics ONLY for genuine subfolders."""
                # Safeguard: Never write a subtotal row for the root directory level
                if current_folder_name == "Root Level":
                    return
                
                writer.writerow([
                    f"SUBTOTAL: {current_folder_name}",
                    sub_qty,
                    self.format_seconds(sub_slicer_secs),
                    self.format_seconds(sub_setup_secs),
                    "", 
                    self.format_seconds(sub_total_secs),
                    f"{sub_grams:.1f}g",
                    f"{sub_passed} passed / {sub_failed} failed"
                ])
                writer.writerow([]) # Clean visual spacer split

            for row in results:
                # Deduce folder mapping relative paths
                rel_path = row.get("relative_path", "")
                if rel_path and "\\" in rel_path:
                    folder_part = rel_path.split("\\")[0]
                elif rel_path and "/" in rel_path:
                    folder_part = rel_path.split("/")[0]
                else:
                    folder_part = "Root Level"

                # Trigger subtotal row when transitioning away from a subfolder
                if current_folder_name is not None and current_folder_name != folder_part:
                    if current_folder_name != "Root Level" and (sub_qty > 0 or sub_failed > 0):
                        write_subtotal_row()
                    
                    # Reset subtotal buckets for the newly encountered directory bracket
                    sub_qty = sub_slicer_secs = sub_setup_secs = sub_total_secs = sub_passed = sub_failed = 0
                    sub_grams = 0.0

                current_folder_name = folder_part

                # Extract file metrics safely
                is_success = row.get("status") == "success"
                model_name = row.get("model", "Unknown")
                
                qty = fallback_flat_qty
                if mode == "Per-Model Manifest File":
                    qty = manifest_map.get(model_name.lower(), fallback_flat_qty)

                slicer_time_secs = int(row.get("print_time_seconds", 0)) if is_success else 0
                setup_overhead_secs = ENDER3_OVERHEAD_SECS if is_success else 0
                unit_total_secs = slicer_time_secs + setup_overhead_secs
                
                scaled_total_secs = unit_total_secs * qty
                scaled_slicer_secs = slicer_time_secs * qty
                scaled_setup_secs = setup_overhead_secs * qty
                
                grams_raw = self.safely_cast_float(row.get("filament_g", 0.0))
                scaled_grams = grams_raw * qty

                # Update subtotal tracks (running silently behind root files too, but won't print)
                sub_qty += qty if is_success else 0
                sub_slicer_secs += scaled_slicer_secs
                sub_setup_secs += scaled_setup_secs
                sub_total_secs += scaled_total_secs
                sub_grams += scaled_grams
                if is_success: sub_passed += 1
                else: sub_failed += 1

                # Update global batch counts
                global_qty += qty if is_success else 0
                global_slicer_secs += scaled_slicer_secs
                global_setup_secs += scaled_setup_secs
                global_total_secs += scaled_total_secs
                global_grams += scaled_grams
                if is_success: global_passed += 1
                else: global_failed += 1

                # Append asset rows
                writer.writerow([
                    model_name,
                    qty if is_success else "",
                    row.get("print_time", "") if is_success else "",
                    self.format_seconds(setup_overhead_secs) if is_success else "",
                    self.format_seconds(unit_total_secs) if is_success else "",
                    self.format_seconds(scaled_total_secs) if is_success else "",
                    f"{scaled_grams:.1f}g" if is_success else "",
                    row.get("status", "failed") if is_success else f"failed: {row.get('error', 'Unknown Error')}"
                ])

            # Catch trailing subtotal brackets if the final files processed were inside a subfolder
            if current_folder_name is not None and current_folder_name != "Root Level" and (sub_qty > 0 or sub_failed > 0):
                write_subtotal_row()

            # Final Grand Totals row configuration
            writer.writerow([])
            writer.writerow([
                "GRAND TOTALS",
                global_qty,
                self.format_seconds(global_slicer_secs),
                self.format_seconds(global_setup_secs),
                "",
                self.format_seconds(global_total_secs),
                f"{global_grams:.1f}g",
                f"{global_passed} passed / {global_failed} failed"
            ])

        return str(output_file)
