# Portable Release Checklist

## Release shape

Portable release ต้องแจกเป็นโฟลเดอร์ `MTChooseWords_Portable` ไม่ใช่ EXE เดี่ยว เพราะโปรแกรมต้องอ่าน/เขียนไฟล์ข้างตัวเอง:

- `MTChooseWords.exe`
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
- ขนาด portable folder ประมาณ 83 MB
- มี `MTChooseWords.exe`, `Run_MTChooseWords.bat`, `config.toml`, SQLite database, fonts, DOCX/TXT sources และ `app/output`
- ไม่มีไฟล์ `.pdf` และ `.doc` ใน portable folder
- ไม่มีโฟลเดอร์ evidence เก่าของ PDF/OCR ใน portable folder
- SQLite database มี 8,705 คำ
- ไม่พบ duplicate key แบบ `ระดับชั้น + normalized word`
- ไม่พบ absolute source path ใน SQLite database
- ไม่พบ absolute path ใน `config.toml`
- Smoke test: `MTChooseWords.exe` ใน portable folder เริ่ม process ได้
- Automated tests: 51 passed
