# OrcaBatchAnalyzer

OrcaBatchAnalyzer is a Windows desktop application that automates batch slicing with OrcaSlicer.

Instead of manually opening, configuring, and slicing every model individually, OrcaBatchAnalyzer uses your existing OrcaSlicer installation and profiles to batch process one or hundreds of STL files, then generates a production-ready report containing print time, material usage, and batch statistics.

No printer profiles need to be exported or maintained separately. The application automatically discovers the printer, process, and filament profiles already configured in OrcaSlicer.

---

# Features

* Automatically detects your OrcaSlicer installation
* Automatically loads your existing printer, process, and filament profiles
* Slice a single STL file or an entire folder of STL files
* Recursively process subfolders
* Automatically orient models before slicing
* Two quantity modes:

  * **Flat Multiplier** – apply the same quantity to every model
  * **Manifest File** – assign different quantities to individual models using a simple text file
* Generates G-code for every successfully processed model
* Produces a comprehensive `results.csv` production report
* Calculates production time, setup overhead, and material usage for the entire batch
* Generates automatic subfolder subtotals for organized multi-project batches
* Optional Performance Mode for improved responsiveness during very large batch analyses
* Continues processing remaining models even if individual files fail

---

# Requirements

* Windows 10 or Windows 11
* [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer/releases) (already set up with your printer, process, and filament profiles)

# Installation

1. Install OrcaSlicer and open it at least once so your profiles exist.
2. Download **OrcaBatchAnalyzer-windows.zip** from the [latest release](../../releases/latest).
3. Unzip it anywhere (for example your Desktop) and double-click **OrcaBatchAnalyzer.exe**.

No Python or Git needed.

> **"Windows protected your PC"?** The app isn't code-signed yet, so SmartScreen may warn on first launch. Click **More info → Run anyway**.

## Build from source (developers)

Requires Python 3.11+ and Git.

```powershell
git clone --recurse-submodules https://github.com/dfktestbot/OrcaBatchAnalyzer.git
cd OrcaBatchAnalyzer
python app.py
```

Do **not** use GitHub's "Download ZIP" button: it leaves out the `vendor/` submodule. If you cloned without `--recurse-submodules`, run `git submodule update --init --recursive`.

To build the exe yourself: `pip install pyinstaller` then `python -m PyInstaller OrcaBatchAnalyzer.spec --noconfirm`. Releases are built automatically by GitHub Actions when a `v*` tag is pushed.

---

# First-Time Setup

The first time the application starts it will automatically:

* Detect your OrcaSlicer installation
* Load your available printer profiles
* Load your available process profiles
* Load your available filament profiles

Simply select the profiles you wish to use.

No additional profile export or configuration is required.

---

# Using OrcaBatchAnalyzer

## Step 1 — Select Profiles

Choose the desired:

* Printer
* Process
* Filament

from the dropdown menus.

---

## Step 2 — Select Input

Choose either:

* A single STL file
* A folder containing STL files

Folders are searched recursively.

---

## Step 3 — Choose a Quantity Strategy

### Flat Multiplier

Apply the same quantity to every discovered model.

Example:

```text
Quantity = 5

100 STL files

↓

500 total calculated parts
```

---

### Manifest File

For different quantities per model, place a file named:

```text
quantities.txt
```

inside the selected input folder.

Example:

```text
gear.stl,10
bracket.stl,2
cover.stl,25
```

Models not listed automatically default to a quantity of **1**.

---

## Step 4 — Select an Output Folder

Choose where generated G-code and reports should be saved.

---

## Step 5 (Optional) — Enable Performance Mode

Performance Mode is recommended for very large jobs (approximately 200+ STL files).

When enabled, the application reduces unnecessary UI updates during processing to improve responsiveness and periodically reclaims unused memory while the batch is running.

The progress indicators remain active while processing continues normally.

---

## Step 6 — Start Processing

Click:

**Start Processing Batch Analysis**

The application will automatically:

* Prepare the selected profiles
* Slice every model
* Generate G-code
* Parse print statistics
* Build the production report

---

# Output

The selected output directory contains:

```text
Output/
├── results.csv
└── Gcode/
    ├── Model_A/
    │   ├── plate_1.gcode
    │   └── slicer.log
    ├── Subfolder__Model_B/      (models in subfolders are prefixed with their folder)
    └── ...
```

The default output folder is `Documents\OrcaBatchAnalyzer\Output`. The app log is at `%LOCALAPPDATA%\OrcaBatchAnalyzer\logs\app.log`.

## `results.csv`

Each processed model includes:

* Model Name
* Qty
* Slicer Print Time
* Machine Setup Constant
* Total Unit Time
* Scaled Total Time
* Total Filament (g)
* status (`success` or `failed`)

If models are organized into subfolders, subtotal rows are inserted for each folder. A final **GRAND TOTALS** row summarizes successfully sliced models: total quantity, total production time (including setup), and total filament.

---

# Troubleshooting

## Slicing completed but no G-code was generated
`[!] Slicing conversion failed` or `Slic3r::CLI::run found error`

OrcaSlicer's command-line interface may reject a model without displaying a graphical error message.

Common causes include:

* The model exceeds the printer's build volume.
* The STL contains multiple independent bodies that require splitting.
* The model contains non-manifold or otherwise invalid geometry.

Each model's full OrcaSlicer output is saved as `slicer.log` in its folder under `Gcode/`; open it first.

To diagnose the issue:

1. Open the model manually in OrcaSlicer using the same printer, process, and filament profiles.
2. Check for warnings or repair prompts.
3. Repair the model if necessary, then rerun the analysis.

---

## OrcaSlicer cannot be found

Install OrcaSlicer normally and restart the application.

If automatic detection fails, manually browse to:

```text
C:\Program Files\OrcaSlicer\orca-slicer.exe
```

---

## No profiles appear in the dropdowns

Open OrcaSlicer, create or save at least one custom printer, process, and filament profile, then restart this app. Only profiles you have saved yourself (not the built-in system presets) are listed.

## "Vendored tool is missing or empty"

You are running from source without the submodule. Run `git submodule update --init --recursive`, or use the release download instead.

---

# Contributing

Bug reports, feature requests, and pull requests are welcome.

When reporting an issue, please include:

* OrcaSlicer version
* App version (or release tag)
* The log file from `%LOCALAPPDATA%\OrcaBatchAnalyzer\logs\app.log`
* Windows version
* Steps to reproduce the issue
