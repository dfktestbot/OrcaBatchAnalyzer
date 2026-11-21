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

Before using OrcaBatchAnalyzer, install:

* Windows 10 or Windows 11
* Python 3.11 or newer
* Git
* OrcaSlicer

---

# Installation

## 1. Open PowerShell

Press **Win + X** and choose **Terminal** or **Windows PowerShell**.

---

## 2. Clone the repository

```powershell
git clone --recurse-submodules https://github.com/dfktestbot/OrcaBatchAnalyzer.git
```

If you already cloned the repository without the required submodule, initialize it by running:

```powershell
git submodule update --init --recursive
```

---

## 3. Open the project folder

```powershell
cd OrcaBatchAnalyzer
```

---

## 4. Verify Python is installed

```powershell
python --version
```

You should see something similar to:

```text
Python 3.11.x
```

---

## 5. Launch the application

```powershell
python app.py
```

If everything is installed correctly, the OrcaBatchAnalyzer window will open.

---

## * One click install

```powershell
winget install --id Git.Git -e --silent; winget install --id Python.Python.3.12 -e --silent; $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User"); cd ~; git clone --recurse-submodules https://github.com/dfktestbot/OrcaBatchAnalyzer.git; cd OrcaBatchAnalyzer; python -m pip install -r requirements.txt; python app.py
```

If everything is installed correctly, the OrcaBatchAnalyzer window will open.

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
    ├── Model_A.gcode
    ├── Model_B.gcode
    └── ...
```

## `results.csv`

Each processed model includes:

* Model Name
* Quantity
* Slicer Print Time
* Machine Setup Time
* Total Unit Time
* Scaled Total Production Time
* Total Filament (g)
* Status

If models are organized into subfolders, OrcaBatchAnalyzer automatically inserts subtotal rows for each folder.

A final **TOTALS** row summarizes the complete production run, including:

* Total models processed
* Total quantity requested
* Total slicer time
* Total setup time
* Total production time
* Total filament required
* Overall processing success

---

# Troubleshooting

## Slicing completed but no G-code was generated
`[!] Slicing conversion failed` or `Slic3r::CLI::run found error`

OrcaSlicer's command-line interface may reject a model without displaying a graphical error message.

Common causes include:

* The model exceeds the printer's build volume.
* The STL contains multiple independent bodies that require splitting.
* The model contains non-manifold or otherwise invalid geometry.

To diagnose the issue:

1. Open the model manually in OrcaSlicer using the same printer, process, and filament profiles.
2. Check for warnings or repair prompts.
3. Repair the model if necessary, then rerun the analysis.

---

## `python` is not recognized

Python is either not installed or was not added to your system PATH.

Download Python:

https://www.python.org/downloads/

During installation, enable:

> **Add python.exe to PATH**

Restart PowerShell after installation.

---

## `git` is not recognized

Download Git for Windows:

https://git-scm.com/download/win

Restart PowerShell after installation.

---

## OrcaSlicer cannot be found

Install OrcaSlicer normally and restart the application.

If automatic detection fails, manually browse to:

```text
C:\Program Files\OrcaSlicer\orca-slicer.exe
```

---

## Missing submodule

If the application reports missing files after cloning, run:

```powershell
git submodule update --init --recursive
```

Then restart the application.

---

# Contributing

Bug reports, feature requests, and pull requests are welcome.

When reporting an issue, please include:

* OrcaSlicer version
* Python version
* Windows version
* Steps to reproduce the issue
