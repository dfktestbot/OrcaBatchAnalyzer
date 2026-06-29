# OrcaBatchAnalyzer

OrcaBatchAnalyzer is a Windows desktop application that automates batch slicing with OrcaSlicer.

Instead of manually opening, configuring, and slicing every model individually, OrcaBatchAnalyzer uses your existing OrcaSlicer installation and profiles to batch process one or hundreds of STL files, then generates a production-ready report of print time and material usage.

No printer profiles need to be exported. The application automatically discovers the printer, process, and filament profiles already configured in OrcaSlicer.

---

# Features

* Automatically detects your OrcaSlicer installation
* Automatically loads your existing printer, process, and filament profiles
* Slice a single STL file or an entire folder of STL files
* Recursively process subfolders
* Automatically orient models before slicing
* Two quantity modes:

  * **Flat Multiplier** – apply the same quantity to every model
  * **Manifest File** – assign different quantities to individual models
* Generates G-code for every successfully processed model
* Produces a production summary spreadsheet (`Results.csv`)
* Calculates total print time, setup time, and material usage for the entire batch
* Efficiently processes large batches without excessive memory usage

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

Press **Win + X** and choose **Windows PowerShell** or **Terminal**.

---

## 2. Clone the repository

Run:

```powershell
git clone --recurse-submodules https://github.com/dfktestbot/OrcaBatchAnalyzer.git
```

If you already cloned the repository without the submodule, run:

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

# First-Time Setup

The first time the application starts:

1. It automatically searches for your OrcaSlicer installation.
2. It automatically loads your available:

   * Printer profiles
   * Process profiles
   * Filament profiles
3. Select the profiles you wish to use.

No profile export or additional configuration is required.

---

# Using OrcaBatchAnalyzer

## Step 1

Choose your:

* Printer
* Process
* Filament

from the dropdown menus.

---

## Step 2

Select your input.

You may choose:

* a single STL file, or
* a folder containing STL files.

Folders are searched recursively.

---

## Step 3

Choose how quantities should be assigned.

### Flat Multiplier

Every model receives the same quantity.

Example:

```
Quantity = 5

100 STL files

↓

500 total printed parts
```

---

### Manifest File

Place a file named:

```
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

## Step 4

Choose an output folder.

---

## Step 5

Click:

**Start Processing Batch Analysis**

The application will automatically:

* prepare the profiles
* slice every model
* calculate production statistics
* generate the final report

---

# Output

The selected output directory will contain:

```text
Output/

├── Results.csv
└── Gcode/
```

`Results.csv` includes:

* Model name
* Quantity
* Estimated slicer print time
* Machine setup time
* Total unit time
* Total production time
* Total filament required (grams)
* Processing status

A final **TOTALS** row summarizes:

* Total models
* Total quantity
* Total slicer time
* Total setup time
* Total production time
* Total filament required

---

# Troubleshooting

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

## The application cannot find OrcaSlicer

Install OrcaSlicer normally and launch the application again.

If automatic detection fails, browse to:

```
C:\Program Files\OrcaSlicer\orca-slicer.exe
```

---

## The application reports missing submodules

Run:

```powershell
git submodule update --init --recursive
```

Then restart the application.

---

# Current Status

OrcaBatchAnalyzer is under active development.

Current functionality includes:

* Automatic OrcaSlicer detection
* Automatic profile discovery
* Native OrcaSlicer CLI integration
* Batch STL processing
* Recursive folder processing
* Flat and manifest quantity strategies
* Automatic model orientation
* Production summary generation

Future updates will focus on additional print-setting overrides, expanded reporting, standalone Windows releases, and further workflow improvements.

---

# Contributing

Bug reports, feature requests, and pull requests are welcome.

When reporting an issue, please include:

* OrcaSlicer version
* Python version
* Windows version
* Steps to reproduce the issue
