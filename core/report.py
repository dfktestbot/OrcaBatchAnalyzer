import csv
from pathlib import Path
from typing import List, Dict, Any
import config

class ProductionReporter:
    """Compiles individual matrix evaluations into standard production CSV sheets."""

    @staticmethod
    def format_seconds(seconds: int) -> str:
        """Converts raw integers back into human scannable formats."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s or not parts: parts.append(f"{s}s")
        return " ".join(parts)

    @staticmethod
    def safely_cast_float(value: str) -> float:
        """Protects math pipelines against unparseable string tokens."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def generate_summary_row(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates all successful analysis entries into an overall summary block."""
        successful = [r for r in results if r["status"] == "success"]

        total_seconds = sum(int(r.get("print_time_seconds", 0)) for r in successful)
        total_mm = sum(self.safely_cast_float(r.get("filament_mm")) for r in successful)
        total_cm3 = sum(self.safely_cast_float(r.get("filament_cm3")) for r in successful)
        total_g = sum(self.safely_cast_float(r.get("filament_g")) for r in successful)
        total_cost = sum(self.safely_cast_float(r.get("filament_cost")) for r in successful)

        return {
            "model": "TOTAL",
            "relative_path": "",
            "print_time": self.format_seconds(total_seconds),
            "print_time_seconds": total_seconds,
            "filament_mm": f"{total_mm:.2f}",
            "filament_cm3": f"{total_cm3:.2f}",
            "filament_g": f"{total_g:.2f}",
            "filament_cost": f"{total_cost:.2f}",
            "gcode_path": "",
            "status": f"{len(successful)} successful / {len(results) - len(successful)} failed",
            "error": ""
        }

    def write_csv_output(self, results: List[Dict[str, Any]]) -> Path:
        """Writes compiled data rows neatly out to disk inside standard output folders."""
        csv_path = config.OUTPUT_DIR / "results.csv"
        rows = results + [self.generate_summary_row(results)]

        fieldnames = [
            "model", "relative_path", "print_time", "print_time_seconds",
            "filament_mm", "filament_cm3", "filament_g", "filament_cost",
            "gcode_path", "status", "error"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return csv_path