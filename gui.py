import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import config
from core.bundle import OrcaProfileManager

class AnalyzerGUI(tk.Tk):
    def __init__(self, run_pipeline_callback):
        super().__init__()
        self.run_pipeline_callback = run_pipeline_callback
        
        self.title("Orca Batch Analyzer")
        self.geometry("680x660") 
        self.minsize(650, 600)
        
        self.style = ttk.Style(self)
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'default')
        
        # State Variables
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(config.OUTPUT_DIR))
        self.orca_exe_path = tk.StringVar(value=config.detect_orca_slicer_path())
        
        self.printer_profile = tk.StringVar()
        self.process_profile = tk.StringVar()
        self.filament_profile = tk.StringVar()
        
        self.quantity_mode = tk.StringVar(value="Flat Multiplier")
        self.flat_quantity = tk.IntVar(value=1)
        self.performance_mode = tk.BooleanVar(value=False) # Performance optimization flag
        
        self._build_ui()
        self._auto_load_system_profiles()
        
    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Section 1: Paths ---
        path_frame = ttk.LabelFrame(main_frame, text=" 1. Workspace Environment Setup ", padding="10")
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="OrcaSlicer Exe:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(path_frame, textvariable=self.orca_exe_path, width=52).grid(row=0, column=1, pady=4, padx=5)
        ttk.Button(path_frame, text="Browse", command=self._browse_orca).grid(row=0, column=2, pady=4, padx=2)
        
        ttk.Label(path_frame, text="Input STL File or Folder:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(path_frame, textvariable=self.input_path, width=52).grid(row=1, column=1, pady=4, padx=5)
        
        btn_frame = ttk.Frame(path_frame)
        btn_frame.grid(row=1, column=2, sticky=tk.W, pady=4, padx=2)
        ttk.Button(btn_frame, text="File", width=6, command=self._browse_stl_file).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="Folder", width=8, command=self._browse_stl_folder).pack(side=tk.LEFT, padx=1)

        ttk.Label(path_frame, text="Analysis Output Dir:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(path_frame, textvariable=self.output_dir, width=52).grid(row=2, column=1, pady=4, padx=5)
        ttk.Button(path_frame, text="Browse", command=self._browse_output).grid(row=2, column=2, pady=4, padx=2)

        # --- Section 2: Profiles & Multipliers ---
        self.profile_frame = ttk.LabelFrame(main_frame, text=" 2. Slicing Config & Batch Quantities ", padding="10")
        self.profile_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.profile_frame, text="Printer Config:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.cb_printer = ttk.Combobox(self.profile_frame, textvariable=self.printer_profile, state="readonly", width=50)
        self.cb_printer.grid(row=0, column=1, columnspan=2, pady=4, padx=5, sticky=tk.W)
        
        ttk.Label(self.profile_frame, text="Slicing Process:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.cb_process = ttk.Combobox(self.profile_frame, textvariable=self.process_profile, state="readonly", width=50)
        self.cb_process.grid(row=1, column=1, columnspan=2, pady=4, padx=5, sticky=tk.W)
        
        ttk.Label(self.profile_frame, text="Material Filament:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.cb_filament = ttk.Combobox(self.profile_frame, textvariable=self.filament_profile, state="readonly", width=50)
        self.cb_filament.grid(row=2, column=1, columnspan=2, pady=4, padx=5, sticky=tk.W)
        
        ttk.Label(self.profile_frame, text="Quantity Strategy:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.cb_qty_mode = ttk.Combobox(self.profile_frame, textvariable=self.quantity_mode, values=["Flat Multiplier", "Per-Model Manifest File"], state="readonly", width=25)
        self.cb_qty_mode.grid(row=3, column=1, sticky=tk.W, pady=4, padx=5)
        self.cb_qty_mode.bind("<<ComboboxSelected>>", self._toggle_qty_visibility)
        
        self.lbl_flat_qty = ttk.Label(self.profile_frame, text="Copies per Model:")
        self.lbl_flat_qty.grid(row=4, column=0, sticky=tk.W, pady=4)
        
        self.ent_flat_qty = ttk.Entry(self.profile_frame, textvariable=self.flat_quantity, width=10)
        self.ent_flat_qty.grid(row=4, column=1, sticky=tk.W, pady=4, padx=5)

        # Optimization Checkbox
        self.chk_perf = ttk.Checkbutton(self.profile_frame, text="Optimize System Resources (Performance Mode - Suspends Live Logs)", variable=self.performance_mode)
        self.chk_perf.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=6, padx=2)

        # --- Section 3: Stationary Progress Interface ---
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=6)
        
        # Text alignment sitting above guarantees the bar never shifts width dynamically
        self.lbl_progress_txt = ttk.Label(self.progress_frame, text="Status: Idle", font=('TkDefaultFont', 9, 'bold'))
        self.lbl_progress_txt.pack(anchor=tk.W, pady=2)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, expand=True)

        # --- Section 4: Status Console ---
        console_frame = ttk.LabelFrame(main_frame, text=" Execution Progress Logs ", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.txt_log = tk.Text(console_frame, height=5, state=tk.DISABLED, background="#f4f4f4", wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll = ttk.Scrollbar(console_frame, command=self.txt_log.yview)
        scroll.pack(fill=tk.Y, side=tk.RIGHT)
        self.txt_log.configure(yscrollcommand=scroll.set)
        
        # --- Run Button ---
        self.btn_run = ttk.Button(main_frame, text="START PROCESSING BATCH ANALYSIS", command=self._trigger_processing)
        self.btn_run.pack(fill=tk.X, pady=5, ipady=5)

    def log(self, message: str, override_perf: bool = False):
        """Logs output to the screen, respects Performance Mode settings."""
        if self.performance_mode.get() and not override_perf:
            return
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def update_progress(self, current: int, total: int, text: str):
        self.progress_bar['maximum'] = total
        self.progress_bar['value'] = current
        percent = (current / total) * 100 if total > 0 else 0
        self.lbl_progress_txt.configure(text=f"[{current}/{total} - {percent:.1f}%]  {text}")

    def _toggle_qty_visibility(self, event=None):
        if self.quantity_mode.get() == "Flat Multiplier":
            self.lbl_flat_qty.grid()
            self.ent_flat_qty.grid()
        else:
            self.lbl_flat_qty.grid_remove()
            self.ent_flat_qty.grid_remove()
            self.log("[NOTE] Manifest Mode activated. Ensure 'quantities.txt' is in your target input folder.", override_perf=True)

    def _browse_orca(self):
        path = filedialog.askopenfilename(filetypes=[("Executables", "*.exe")])
        if path: self.orca_exe_path.set(path)
        
    def _browse_stl_file(self):
        path = filedialog.askopenfilename(filetypes=[("3D Models", "*.stl")])
        if path: self.input_path.set(path)
        
    def _browse_stl_folder(self):
        path = filedialog.askdirectory()
        if path: self.input_path.set(path)
        
    def _browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)

    def _auto_load_system_profiles(self):
        _, _, user_dir = config.get_orca_roaming_paths()
        try:
            config.ensure_directories()
            manager = OrcaProfileManager()
            profile_data = manager.discover_user_profiles(user_dir)
            
            self.cb_printer['values'] = profile_data["printer"]
            self.cb_process['values'] = profile_data["process"]
            self.cb_filament['values'] = profile_data["filament"]
            
            if profile_data["printer"]: self.cb_printer.current(0)
            if profile_data["process"]: self.cb_process.current(0)
            if profile_data["filament"]: self.cb_filament.current(0)
            
            self.log("[✓] Local printer profiles dynamically synchronized.", override_perf=True)
        except Exception as e:
            self.log(f"[!] Profile Sync Failure: {e}", override_perf=True)

    def _trigger_processing(self):
        if not self.orca_exe_path.get() or not self.input_path.get():
            messagebox.showwarning("Missing Variables", "Please define your Orca Executable and target Input files.")
            return
            
        if self.quantity_mode.get() == "Flat Multiplier":
            try:
                if self.flat_quantity.get() < 1: raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showwarning("Invalid Input", "Please provide a valid flat quantity multiplier (Minimum 1).")
                return
        
        self.btn_run.configure(state=tk.DISABLED)
        config.OUTPUT_DIR = Path(self.output_dir.get())
        config.GCODE_DIR = config.OUTPUT_DIR / "Gcode"
        
        worker_thread = threading.Thread(
            target=self.run_pipeline_callback, 
            args=(self,), 
            daemon=True
        )
        worker_thread.start()
