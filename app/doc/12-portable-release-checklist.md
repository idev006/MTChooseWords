# Portable Release Checklist

## Release shape

Portable release ต้องแจกเป็นโฟลเดอร์ `MTChooseWords_Portable` ไม่ใช่ EXE เดี่ยว เพราะโปรแกรมต้องอ่าน/เขียนไฟล์ข้างตัวเอง:

- `MTChooseWords.exe` และ PyInstaller runtime files ข้าง EXE
- `Run_MTChooseWords.bat`
- `config.toml`
- `app/mtchoosewords.sqlite3`
- `app/assets/fonts`
- `app/assets/words/lot1` เฉพาะ `.docx`
- `app/assets/words/text` เฉพาะ `.txt`
- `app/assets/words/reviewed_suspicions.json`
- `app/doc`
- `app/output`

## Build command

```powershell
.\.venv\Scripts\python.exe scripts\build_portable.py
```

หรือดับเบิลคลิก:

```text
Build_Portable_MTChooseWords.bat
```

## Must not include

- `.venv`
- `build`
- PDF source files
- legacy `.doc` source files
- retired PDF/OCR evidence folders
- Python cache folders
- local test output

## Acceptance checks

- เปิด `dist/MTChooseWords_Portable\Run_MTChooseWords.bat` ได้
- แตก `dist\MTChooseWords_Portable.zip` ไป path ใหม่ แล้วเปิด `Run_MTChooseWords.bat` ได้
- ต้องเห็นหน้าต่างโปรแกรมจริง ไม่ใช่ตรวจแค่ process
- สร้าง `dist\MTChooseWords_Portable.zip` สำหรับส่งต่อได้
- โปรแกรมเห็นจำนวนคำใน database
- เลือกฟอนท์ได้จาก `app/assets/fonts`
- สร้างใบงานลง `app/output`
- ย้ายโฟลเดอร์ `MTChooseWords_Portable` ไป path ใหม่แล้วยังเปิดได้
- `config.toml`, reports, journals และ SQLite `source_file` ไม่มี absolute path ของเครื่องพัฒนา

## Latest readiness result

ผลตรวจล่าสุดวันที่ 2026-08-29:

- สร้าง `dist/MTChooseWords_Portable` สำเร็จ
- สร้าง `dist/MTChooseWords_Portable.zip` สำเร็จ
- ใช้ PyInstaller one-dir runtime เพื่อให้ Qt DLL อยู่ข้าง EXE และลดความเสี่ยง `QtCore` DLL load error
- กัน `icudt78.dll` และ `icuuc.dll` ไม่ให้ถูก bundle จาก runtime อื่นในเครื่องพัฒนา เพราะเคยทำให้ `PySide6.QtCore` ขึ้น `DLL load failed`
- ZIP ขนาดประมาณ 63.8 MB
- มี 291 ไฟล์ใน portable folder เพราะใช้ PyInstaller one-dir runtime
- มี `MTChooseWords.exe`, PyInstaller runtime files, `Run_MTChooseWords.bat`, `config.toml`, SQLite database, fonts, DOCX/TXT sources และ `app/output`
- ไม่มี `icu*.dll` ใน portable `_internal`
- ไม่มีไฟล์ `.pdf` และ `.doc` ใน portable folder
- ไม่มีโฟลเดอร์ evidence เก่าของ PDF/OCR ใน portable folder
- SQLite database มี 8,705 คำ
- ไม่พบ duplicate key แบบ `ระดับชั้น + normalized word`
- ไม่พบ absolute source path ใน SQLite database
- ไม่พบ absolute path ใน `config.toml`
- Visual smoke test: แตก ZIP ไป Temp path ใหม่ เปิด `Run_MTChooseWords.bat`, เห็นหน้าต่าง `MT Choose Words — สร้าง PDF คำศัพท์` พร้อม tab นำเข้า/สร้างใบงาน และไม่เกิด error dialog `QtCore`
- Screenshot evidence: `C:\Users\66996\AppData\Local\Temp\mtchoosewords_portable_ui_visible_after_icu_fix.png`
- Automated tests: 51 passed in 34.96s
