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

    @staticmethod
    def _last(pattern, text):
        matches = list(pattern.finditer(text))
        return matches[-1] if matches else None

    @staticmethod
    def _read_metadata_text(gcode_file: Path, tail_bytes: int = 1_000_000, head_bytes: int = 64_000) -> str:
        """Reads only the end (and, as a fallback, the start) of the file so huge G-code isn't loaded into memory."""
        with open(gcode_file, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - tail_bytes))
            tail = f.read().decode("utf-8", errors="ignore")
            head = ""
            if size > tail_bytes:
                f.seek(0)
                head = f.read(head_bytes).decode("utf-8", errors="ignore")
        return head + "\n" + tail

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

        status = "success"
        error_msg = ""
        try:
            footer_text = self._read_metadata_text(gcode_file)

            t_match = self._last(time_pat, footer_text)
            mm_match = self._last(mm_pat, footer_text)
            cm3_match = self._last(cm3_pat, footer_text)
            g_match = self._last(g_pat, footer_text)
            cost_match = self._last(cost_pat, footer_text)

            if t_match: print_time = t_match.group(1).strip()
            if mm_match: filament_mm = mm_match.group(1).strip()
            if cm3_match: filament_cm3 = cm3_match.group(1).strip()
            if g_match: filament_g = g_match.group(1).strip()
            if cost_match: filament_cost = cost_match.group(1).strip()

            # A G-code file without these stats would otherwise be reported as a
            # "success" with zero time and zero filament, silently skewing the totals.
            if not print_time and not filament_g:
                status = "failed"
                error_msg = "G-code was generated but contains no print time or filament statistics"
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