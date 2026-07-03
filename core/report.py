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

    def write_csv_output(self, analysis_results, input_path_str, mode, fallback_flat_qty):
    output_csv_path = Path(config.OUTPUT_DIR) / "results.csv"
    
    # 1. Bucket assets safely into Root vs Subfolders
    root_files = []
    subfolder_groups = {}
    
    for result in analysis_results:
        rel_path = Path(result.get("relative_path", ""))
        if len(rel_path.parents) > 1:
            subfolder_name = rel_path.parts[0]
            if subfolder_name not in subfolder_groups:
                subfolder_groups[subfolder_name] = []
            subfolder_groups[subfolder_name].append(result)
        else:
            root_files.append(result)

    # 2. Compile and write the structural layout
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Standard Column Headers
        writer.writerow(["Model Name", "Qty", "Slicer Print Time", "Machine Setup Constant", "Total Unit Time", "Scaled Total Time", "Total Filament (g)", "status"])
        
        # --- BLOCK 1: LOOSE ROOT FILES ---
        if root_files:
            writer.writerow([]) # Cushion row below column headers
            for r in root_files:
                # Keep original model name clean for root level
                writer.writerow(self._build_row_data(r, r.get("model"), mode, fallback_flat_qty))
        
        # --- BLOCK 2: SUBFOLDER BATCHES ---
        for folder_name, items in subfolder_groups.items():
            writer.writerow([]) # Clear visual break before a new subfolder group block starts
            writer.writerow([f"FOLDER: {folder_name}"]) # Section Header Row
            
            folder_qty = folder_secs = 0
            folder_grams = 0.0
            
            for r in items:
                # Indent subfolder files visually using the tree character
                indented_name = f"└── {r.get('model')}"
                writer.writerow(self._build_row_data(r, indented_name, mode, fallback_flat_qty))
                
                if r.get("status") == "success":
                    # ... your existing folder subtotal math accumulation goes here ...
                    pass
            
            # Write out the group subtotal row right underneath its items
            writer.writerow([f"SUBTOTAL: {folder_name}", folder_qty, "", "", "", folder_secs, folder_grams, ""])
        
        # --- BLOCK 3: GRAND TOTALS ---
        writer.writerow([]) # Clear break before the final grand calculations summary
        # ... your existing grand totals row insertion logic goes here ...
        
    return output_csv_path
