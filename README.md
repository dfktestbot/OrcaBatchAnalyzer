# Orca Batch Analyzer

A high-performance, memory-safe Python automation tool and Tkinter GUI designed to batch-slice an entire folder of 3D models (`.stl`) using your local OrcaSlicer profiles. It extracts critical print telemetry (total filament usage in grams, printing time, and material cost) and compiles it into an organized production CSV spreadsheet.

## 🛠️ Features

- **Recursive Folder Scanning**: Automatically crawls nested directory trees to find and isolate all `.stl` assets.
- **Dynamic Profile Discovery**: Reads and maps your custom OrcaSlicer printer, process, and filament configurations directly from your local `%APPDATA%` path at runtime.
- **Memory-Safe G-Code Parsing**: Streams and reads only the tail execution buffers of generated G-code files, avoiding system stutters or out-of-memory overhead on massive multi-hundred-megabyte files.
- **Profile Signature Bypass**: Patches and strips restricted system keys from temporary profile configuration dictionaries to satisfy OrcaSlicer's strict security checks.

## 📖 User Tutorial & Workflow

Running a batch analysis takes under a minute. Here is exactly how to navigate the interface:

### Step 1: Select Your Working Paths
When you launch `python app.py`, the Tkinter graphical interface will open.
1. **Input Directory**: Click **Browse** and select the folder containing your `.stl` models. The app will recursively find all models hidden inside any subfolders.
2. **Output Directory**: Click **Browse** and choose where you want your final production spreadsheet (`results.csv`) to be saved.

### Step 2: Configure Slicing Profiles
The dropdown menus automatically scan your local OrcaSlicer installation at runtime to find your personal, custom profiles. 
- Select your target **Printer** model.
- Select your desired **Process**
- Select your active **Filament** profile.
- **Note**: these config settings are all pulled directly from your local orca slicer instance and mirror whatever settings you have chosen there.

### Step 3: Run the Pipeline
Click the **START PROCESSING BATCH ANALYSIS** button at the bottom. 

```text
[  App Console Log Window  ]
├── [INFO] Found 14 STL models to process.
├── [SLICING] Processing: bracket_v2.stl... Done.
├── [SLICING] Processing: enclosure_base.stl... Done.
└── [SUCCESS] Extraction complete. Compiling results.csv...
