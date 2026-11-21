# PyInstaller spec: one-folder, windowed build.
# Build:  python -m PyInstaller OrcaBatchAnalyzer.spec --noconfirm
import os

spec_dir = os.path.abspath(SPECPATH)
vendor_rel = os.path.join("vendor", "orcaslicer-filament-tool")
vendor_abs = os.path.join(spec_dir, vendor_rel)

if not os.path.isfile(os.path.join(vendor_abs, "src", "cli.py")):
    raise SystemExit(
        f"Vendored tool not found at {vendor_abs}\n"
        "Run: git submodule update --init --recursive"
    )

a = Analysis(
    [os.path.join(spec_dir, "app.py")],
    # vendor_abs on the path lets PyInstaller resolve the tool's `src` package and trace its imports.
    pathex=[spec_dir, vendor_abs],
    # The tool is only ever run via runpy at runtime, so nothing imports it statically.
    hiddenimports=["src.cli"],
    # Also ship its files as data: it may read files relative to its own folder.
    datas=[(vendor_abs, vendor_rel)],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OrcaBatchAnalyzer",
    console=False,      # windowed app. Set True temporarily to debug a broken build.
    upx=False,          # UPX-packed exes trigger far more antivirus false positives
    # icon="assets/icon.ico",
)
coll = COLLECT(exe, a.binaries, a.datas, name="OrcaBatchAnalyzer", upx=False)
