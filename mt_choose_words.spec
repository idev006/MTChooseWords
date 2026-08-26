# Build with: .venv/Scripts/python.exe -m PyInstaller mt_choose_words.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
root = Path(SPEC).resolve().parent
datas = [
    (str(root / "config.toml"), "."),
    (str(root / "app" / "assets"), "app/assets"),
]
datas += collect_data_files("pythainlp")
hiddenimports = ["pdfplumber", "pdfminer", "pypdfium2", "pythainlp"]

a = Analysis(
    [str(root / "app" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MTChooseWords",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
