# OrcaBatchAnalyzer

OrcaBatchAnalyzer is a desktop application that automates batch slicing with OrcaSlicer.

Instead of manually opening, configuring, and slicing every model individually, OrcaBatchAnalyzer uses your existing OrcaSlicer installation and profile settings to batch process one or hundreds of STL files, then generates a production-ready summary of print time and material usage.

No printer profiles need to be exported, edited, or maintained separately—the application automatically discovers the profiles already configured in your OrcaSlicer installation.

---

# Features

* Automatically detects your OrcaSlicer installation
* Automatically discovers your existing printer, process, and filament profiles
* Slice a single STL file or an entire directory of STL files
* Recursively process subfolders
* Automatically orient models before slicing
* Choose between two quantity strategies:

  * **Flat Multiplier** – apply the same quantity to every model
  * **Manifest File** – specify different quantities for individual models using a simple text file
* Generates G-code for every successfully processed model
* Produces a production summary CSV for the entire batch
* Efficiently processes large batches without loading every generated G-code file into memory at once

---

# Requirements

* Windows
* Python 3.11 or newer
* OrcaSlicer installed and configured

---

# Installation

Clone the repository together with its required submodule:

```bash
git clone --recurse-submodules https://github.com/dfktestbot/OrcaBatchAnalyzer.git
```

If you already cloned the repository without submodules, initialize them with:

```bash
git submodule update --init --recursive
```

Currently, no additional third-party Python packages are required beyond a standard Python installation.

---

# Getting Started

1. Install and configure OrcaSlicer normally.
2. Launch OrcaBatchAnalyzer:

```bash
python app.py
```

3. The application automatically loads your available:

   * Printer profiles
   * Process profiles
   * Filament profiles

4. Select the profiles you want to use.

5. Select either:

   * A single STL file, or
   * A folder containing STL files (processed recursively).

6. Choose a quantity strategy.

### Option 1 – Flat Multiplier

Apply the same quantity to every discovered model.

Example:

```
Quantity = 5

100 STL files

↓

500 total printed parts
```

### Option 2 – Manifest File

Place a file named `quantities.txt` inside the selected input folder.

Example:

```text
gear.stl,10
bracket.stl,2
cover.stl,25
```

Any model not listed will automatically default to a quantity of **1**.

7. Choose an output folder.

8. Click **Start Processing Batch Analysis**.

---

# Output

The selected output directory contains:

```text
Output/

├── Results.csv
└── Gcode/
    ├── ...
```

`Results.csv` contains production information for every successfully processed model, including:

* Model name
* Quantity
* Estimated slicer print time
* Machine setup time
* Total unit time
* Scaled production time
* Total filament required (grams)
* Processing status

A final **TOTALS** row summarizes the entire batch, including:

* Total models processed
* Total quantity requested
* Total slicer print time
* Total machine setup time
* Total production time
* Total filament required

---

# Notes

* Your OrcaSlicer configuration is **never modified**.
* The application automatically reads your existing OrcaSlicer profiles.
* Temporary files are generated only while processing and are cleaned up automatically.
* Automatic model orientation is enabled by default.
* Individual processing failures do not stop the remainder of the batch from completing.

---

# Current Status

OrcaBatchAnalyzer is under active development.

Current functionality includes:

* Automatic OrcaSlicer detection
* Automatic profile discovery
* Batch STL processing
* Quantity scaling
* Recursive directory processing
* Native OrcaSlicer CLI integration
* Production summary generation

Planned improvements include:

* Standalone Windows executable
* Option to load generic default settings
* more as things come up

---

# Contributing

Bug reports, feature requests, and pull requests are welcome.

When reporting an issue, please include:

* OrcaSlicer version
* Python version
* Windows version
* Steps to reproduce the issue

