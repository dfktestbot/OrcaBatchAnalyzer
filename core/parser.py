import re
from pathlib import Path
from typing import Dict, Any

class GCodeAnalyticParser:
    """Parses output metrics directly out of finished print execution files efficiently."""

    @staticmethod
    def parse_time_to_seconds(time_text: str) -> int:
        """Translates localized text variations like '1h 24m 5s' to exact total integer counts."""
        if not time_text:
            return 0
        total = 0
        hours = re.search(r"(\d+)\s*h", time_text)
        minutes = re.search(r"(\d+)\s*m", time_text)
        seconds = re.search(r"(\d+)\s*s", time_text)

        if hours:
            total += int(hours.group(1)) * 3600
        if minutes:
            total += int(minutes.group(1)) * 60
        if seconds:
            total += int(seconds.group(1))
        return total

    def process_gcode_file(self, gcode_file: Path, base_model_path: Path, relative_input_root: Path) -> Dict[str, Any]:
        """Extracts print telemetry keys safely out of raw sliced metadata records by scanning the file tail."""
        
        # Initialize default blanks
        print_time = ""
        filament_mm = ""
        filament_cm3 = ""
        filament_g = ""
        filament_cost = ""

        # Compiled regexes for performance
        time_pat = re.compile(r"; estimated printing time \(normal mode\) = (.+)")
        mm_pat = re.compile(r"; filament used \[mm\] = ([\d.]+)")
        cm3_pat = re.compile(r"; filament used \[cm3\] = ([\d.]+)")
        g_pat = re.compile(r"; filament used \[g\] = ([\d.]+)")
        cost_pat = re.compile(r"; filament cost = ([\d.]+)")

        # Read the file line by line or from the tail block to save system memory.
        # Since OrcaSlicer puts these comments right at the end of the file, we parse them smoothly.
        try:
            with open(gcode_file, "r", encoding="utf-8", errors="ignore") as f:
                # Read the last 2000 lines, which safely covers the entire footer metadata envelope
                lines = f.readlines()[-2000:]
                
            footer_text = "".join(lines)
            
            t_match = time_pat.search(footer_text)
            mm_match = mm_pat.search(footer_text)
            cm3_match = cm3_pat.search(footer_text)
            g_match = g_pat.search(footer_text)
            cost_match = cost_pat.search(footer_text)

            if t_match: print_time = t_match.group(1).strip()
            if mm_match: filament_mm = mm_match.group(1).strip()
            if cm3_match: filament_cm3 = cm3_match.group(1).strip()
            if g_match: filament_g = g_match.group(1).strip()
            if cost_match: filament_cost = cost_match.group(1).strip()
            
            status = "success"
            error_msg = ""
        except Exception as e:
            status = "failed"
            error_msg = str(e)

        return {
            "model": base_model_path.name,
            "relative_path": str(base_model_path.relative_to(relative_input_root)),
            "print_time": print_time,
            "print_time_seconds": self.parse_time_to_seconds(print_time),
            "filament_mm": filament_mm,
            "filament_cm3": filament_cm3,
            "filament_g": filament_g,
            "filament_cost": filament_cost,
            "gcode_path": str(gcode_file),
            "status": status,
            "error": error_msg
        }