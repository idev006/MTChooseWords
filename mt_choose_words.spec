# Build with: .venv/Scripts/python.exe -m PyInstaller mt_choose_words.spec
from pathlib import Path
root = Path(SPEC).resolve().parent
datas = []
hiddenimports = []

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
a.binaries = [
    item for item in a.binaries
    if Path(item[0]).name.lower() not in {"icudt78.dll", "icuuc.dll"}
]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MTChooseWords",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="MTChooseWords",
)
