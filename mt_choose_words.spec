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
