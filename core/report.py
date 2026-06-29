import csv
import os
from pathlib import Path
from typing import List, Dict, Any
import config

class ProductionReporter:
    """Compiles individual matrix evaluations into streamlined print production CSV sheets."""

    @staticmethod
    def format_seconds(seconds: int) -> str:
        """Converts raw integers back into human scannable layouts."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s or not parts: parts.append(f"{s}s")
        return " ".join(parts)

    @staticmethod
    def safely_cast_float(value: Any) -> float:
        """Protects math pipelines against unparseable string tokens."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _load_manifest_quantities(self, input_source_path: Path) -> Dict[str, int]:
        """
        Parses an optional 'quantities.txt' manifest file inside the input path.
        Expected line format: bracket_v2.stl, 5
        """
        manifest_map = {}
        target_dir = input_source_path if input_source_path.is_dir() else input_source_path.parent
        manifest_file = target_dir / "quantities.txt"
        
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "," in line:
                            parts = line.strip().split(",", 1)
                            stl_name = parts[0].strip().lower()
                            try:
                                qty = int(parts[1].strip())
                                if qty >= 1:
                                    manifest_map[stl_name] = qty
                            except ValueError:
                                continue
            except Exception as e:
                print(f"[!] Error reading quantities.txt manifest file: {e}")
                
        return manifest_map

    def generate_summary_row(self, results: List[Dict[str, Any]], total_qty: int, total_slicer_secs: int, total_overhead_secs: int, total_g: float) -> Dict[str, Any]:
        """Compiles the final aggregation totals block."""
        successful_count = len([r for r in results if r.get("status") == "success"])
        total_combined_secs = total_slicer_secs + total_overhead_secs
        
        return {
            "Model Name": "TOTALS",
            "Qty": total_qty,
            "Slicer Print Time": self.format_seconds(total_slicer_secs),
            "Machine Setup Constant": self.format_seconds(total_overhead_secs),
            "Total Unit Time": "",
            "Scaled Total Time": self.format_seconds(total_combined_secs),
            "Total Filament (g)": f"{total_g:.1f}g",
            "status": f"{successful_count} passed / {len(results) - successful_count} failed"
        }

    def write_csv_output(self, results: List[Dict[str, Any]], input_path_str: str, mode: str, fallback_flat_qty: int) -> Path:
        """Processes, maps quantities via flat or manifest files, attaches constants, and outputs rows."""
        csv_path = config.OUTPUT_DIR / "results.csv"
        ENDER3_OVERHEAD_SECS = 300 
        
        manifest_map = {}
        if mode == "Per-Model Manifest File":
            manifest_map = self._load_manifest_quantities(Path(input_path_str))
        
        formatted_rows = []
        total_qty = 0
        total_slicer_secs = 0
        total_overhead_secs = 0
        total_g = 0.0

        for run in results:
            model_filename = run.get("model", "Unknown")
            
            # Determine appropriate quantity using requested strategy
            if mode == "Per-Model Manifest File":
                qty = manifest_map.get(model_filename.lower(), 1)  # Fallback to 1 if missing from text document
            else:
                qty = int(fallback_flat_qty)

            if run.get("status") == "success":
                raw_slicer_secs = int(run.get("print_time_seconds", 0))
                raw_grams = self.safely_cast_float(run.get("filament_g", 0.0))
                
                # Math overhead configurations
                unit_total_secs = raw_slicer_secs + ENDER3_OVERHEAD_SECS
                scaled_total_secs = unit_total_secs * qty
                scaled_grams = raw_grams * qty
                
                # Accumulate systems parameters
                total_qty += qty
                total_slicer_secs += (raw_slicer_secs * qty)
                total_overhead_secs += (ENDER3_OVERHEAD_SECS * qty)
                total_g += scaled_grams
                
                formatted_rows.append({
                    "Model Name": model_filename,
                    "Qty": qty,
                    "Slicer Print Time": self.format_seconds(raw_slicer_secs),
                    "Machine Setup Constant": self.format_seconds(ENDER3_OVERHEAD_SECS),
                    "Total Unit Time": self.format_seconds(unit_total_secs),
                    "Scaled Total Time": self.format_seconds(scaled_total_secs),
                    "Total Filament (g)": f"{scaled_grams:.1f}g",
                    "status": "success"
                })
            else:
                formatted_rows.append({
                    "Model Name": model_filename,
                    "Qty": qty,
                    "Slicer Print Time": "--",
                    "Machine Setup Constant": "--",
                    "Total Unit Time": "--",
                    "Scaled Total Time": "--",
                    "Total Filament (g)": "--",
                    "status": f"failed: {run.get('error', 'Unknown Error')}"
                })

        summary_row = self.generate_summary_row(results, total_qty, total_slicer_secs, total_overhead_secs, total_g)

        fieldnames = [
            "Model Name", "Qty", "Slicer Print Time", "Machine Setup Constant",
            "Total Unit Time", "Scaled Total Time", "Total Filament (g)", "status"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(formatted_rows)
            writer.writerow({})
            writer.writerow(summary_row)

        return csv_path
