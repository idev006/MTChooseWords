# Test Cases และ Test Report

## 1. Test strategy

ใช้การทดสอบ 5 ระดับ:

1. Unit test: config, repository, layout geometry และ adapter contracts
2. Contract test: ตรวจ source contract, canonical grade key, trim, duplicate และ fail-closed gate
3. Certification test: อ่าน DOCX/TXT source จริงและตรวจ baseline จำนวนคำ
4. Export test: สร้าง PDF จริงและตรวจจำนวนหน้า/ไฟล์
5. Build smoke test: สร้าง executable ด้วย PyInstaller

## 2. Test cases

| ID | ระดับ | กรณีทดสอบ | Expected result |
|---|---|---|---|
| TC-001 | Unit | บันทึกและโหลด TOML | ค่า config กลับมาตรงกัน |
| TC-002 | Unit | insert คำซ้ำ | เหลือคำ unique เท่านั้น |
| TC-003 | Unit | reload repository | ข้อมูลเก่าถูกแทนที่ด้วยชุดใหม่ |
| TC-004 | Unit | ตรวจ adapter contracts | extractor/exporter/repository มี method ตาม contract |
| TC-005 | Unit | จัดวางคำหลายคำ | ได้จำนวนคำตามต้องการ |
| TC-006 | Unit | ตรวจ bounding boxes | ไม่มีคู่ใด intersect กัน |
| TC-007 | Unit | DOCX table-only extraction | อ่านเฉพาะ cell คำในตาราง |
| TC-008 | Unit | Thai normalizer no-guess policy | ไม่เดาซ่อมคำสะกดจาก PDF mapping เก่า |
| TC-009 | Unit | Unsupported PDF source | importer ไม่รับ `.pdf` เป็น source คำ |
| TC-010 | Export | สร้าง PDF 2 หน้า | PDF มี 2 หน้าและมีขนาดไฟล์มากกว่า 0 |
| TC-011 | Build | PyInstaller spec | สร้าง `dist/MTChooseWords.exe` สำเร็จ |
| TC-012 | Regression | Removed PDF repair dictionary | คำอย่าง `ตาลึง` และ `กานัน` ต้องไม่ถูกเดาแก้ |
| TC-013 | Regression | Removed PDF/OCR dependencies | `requirements.txt` และ PyInstaller spec ไม่มี dependency ของ PDF/OCR reader |
| TC-014 | Unit | DOCX มีข้อความนอกตารางและตารางคำ | อ่านเฉพาะ cell คำในตาราง |
| TC-015 | Unit | คำเดียวกันอยู่คนละระดับชั้น | เก็บและกรองตามระดับชั้นได้ |
| TC-016 | Unit | Source ไม่มีระดับชั้นในชื่อไฟล์ | Import ล้มเหลวแบบ fail-closed |
| TC-017 | Unit | โฟลเดอร์มี `.docx` และ `.doc` | อ่าน `.docx` และไม่อ่าน `.doc` |
| TC-018 | Evidence | Reload source จริง | สร้าง `word_import_report.json` พร้อม counts/source files |
| TC-019 | Unit | Append import | เพิ่มคำใหม่โดยไม่ล้างคำเดิมและไม่เพิ่ม duplicate key |
| TC-020 | Unit | Corrupt text layer character | Source contract ปฏิเสธอักขระผิดปกติ |
| TC-021 | Unit | Long wrapped word cell | อ่านได้และ mark เป็น `long_cell_review` |
| TC-022 | Unit | TXT source | อ่านหนึ่งคำต่อหนึ่งบรรทัด, trim คำ และใช้เลขบรรทัดเป็น source index |
| TC-023 | Unit | Production adapter registry | รองรับ `.docx`/`.txt` และไม่รับ `.pdf` ใน production |
| TC-024 | Unit | Removed PDF diagnostic registry | ไม่มี diagnostic registry สำหรับ PDF adapter |
| TC-025 | Evidence | Source-folder journal | audit/reload ต้องสร้าง `mtchoosewords_import_journal.json` พร้อม grade key แบบ `ป.x` |
| TC-026 | Regression | DOCX+TXT duplicate ในระดับเดียวกัน | นับ duplicate ข้าม source ด้วย key `ป.x + normalized word` |
| TC-027 | Regression | Database key canonical | ฐานข้อมูลเก็บ `grade` เป็น `ป.1`-`ป.6` และ trim คำก่อนบันทึก |
| TC-028 | Migration | Old integer grade schema | ฐานข้อมูล schema เก่าที่ใช้ integer grade ถูก rebuild เป็น text grade key |
| TC-029 | Config | Committed config production-safe | `config.toml` ต้องชี้ DOCX/TXT source, ไม่ชี้ PDF, และใช้ฐานข้อมูลโครงการ |
| TC-030 | Certification | Real DOCX+TXT source baseline | Source จริง 12 ไฟล์ต้องอ่านได้ 14,374 cells, 8,705 unique words, 5,669 duplicate cells |
| TC-031 | Certification | Committed SQLite baseline | `app/mtchoosewords.sqlite3` ต้องมี 8,705 คำ, grade เป็น `ป.x`, ไม่มี duplicate key และไม่มี trim violation |
| TC-032 | Unit | Import worker from UI button | ปุ่ม “นำเข้ารายการคำ” ต้องเพิ่มคำโดยไม่ล้าง database |
| TC-033 | Unit | Clear worker from UI button | ปุ่ม “ล้างข้อมูลคำในฐานข้อมูล” ต้องล้างอย่างเดียวและไม่ import คำ |
| TC-034 | UI smoke | Import tab button labels | หน้าต่างจริงต้องมีปุ่ม “ล้างข้อมูลคำในฐานข้อมูล” และ “นำเข้ารายการคำ” โดยไม่มี checkbox ล้างก่อน Reload |
| TC-035 | Unit | PathManager relative conversion | Path ใต้ project root ต้องถูกบันทึกเป็น relative และ path นอก root ต้องคงค่าไว้ |
| TC-036 | Certification | Portable evidence/database paths | Config, journal, report และ SQLite `source_file` ต้องไม่มี absolute project path |
| TC-037 | Unit | Removed local PDF/OCR reader | ไม่มี core reader, script หรือ evidence generator สำหรับอ่านคำจาก PDF/OCR |
| TC-038 | Portable visual smoke | แตก ZIP ไป Temp path ใหม่และเปิดด้วย batch file | ต้องเห็นหน้าต่างโปรแกรมจริงและไม่มี error dialog `QtCore` |

## 3. Test result — 2026-07-26

คำสั่ง:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

ผลลัพธ์:

```text
28 passed in 62.76s
```

ครอบคลุม TC-001 ถึง TC-018 ใน automated tests และ reload evidence

คำสั่ง build:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm mt_choose_words.spec
```

ผลลัพธ์: **ผ่าน** — สร้าง `dist/MTChooseWords.exe` สำเร็จ

## 4. Test result — 2026-08-28

คำสั่ง:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

ผลลัพธ์:

```text
54 passed
```

Certification baseline:

```text
DOCX/TXT production sources: 12 files
Source cells/lines: 14,374
Unique words after normalized key: 8,705
Duplicate cells/lines removed: 5,669
Committed SQLite rows: 8,705
Trim violations: 0
```

คำสั่ง reload ที่ใช้ตรวจ config production:

```powershell
.\.venv\Scripts\python.exe scripts\reload_words.py
```

ผลลัพธ์:

```text
Reload complete (clear-all): 8705 unique words
Source cells: 14374; duplicates removed: 5669
```

## 5. Test result — 2026-08-29

คำสั่ง:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

ผลลัพธ์:

```text
51 passed in 23.26s
```

Certification baseline:

```text
DOCX/TXT production sources: 12 files
Source cells/lines: 14,374
Unique words after normalized key: 8,705
Duplicate cells/lines removed: 5,669
Committed SQLite rows: 8,705
Absolute source paths: 0
Trim violations: 0
```

คำสั่ง reload ที่ใช้ตรวจ config production:

```powershell
.\.venv\Scripts\python.exe scripts\reload_words.py
```

ผลลัพธ์:

```text
Reload complete (clear-all): 8705 unique words
Source cells: 14374; duplicates removed: 5669
```

คำสั่ง build:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mt_choose_words.spec
```

ผลลัพธ์: **ผ่าน** — สร้าง `dist/MTChooseWords.exe` สำเร็จ

Portable readiness:

```text
dist/MTChooseWords_Portable created from PyInstaller one-dir runtime
dist/MTChooseWords_Portable.zip created
Portable zip size: about 63.8 MB
Portable file count: 291
SQLite rows: 8,705
Duplicate grade+word keys: 0
Absolute source paths: 0
PDF files in portable folder: 0
DOC files in portable folder: 0
Retired PDF/OCR evidence folders: 0
Portable _internal icu*.dll files: 0
Portable visual smoke test from extracted Temp folder: visible UI window `MT Choose Words — สร้าง PDF คำศัพท์`
QtCore error dialog: not found
Screenshot evidence: C:\Users\66996\AppData\Local\Temp\mtchoosewords_portable_ui_visible_after_icu_fix.png
```

## 6. Manual test cases ที่ยังต้องทำบน OS อื่น

- เปิด UI บน macOS และ Linux
- เลือกฟอนท์ผ่าน dialog
- กด Reload จาก UI และตรวจ status/progress
- คลิกปุ่มนำเข้า/ล้างข้อมูลบน packaged EXE พร้อม test database สำเนา
- สร้าง PDF แนวตั้งและแนวนอน
- เปิด PDF ด้วย viewer ของแต่ละ OS
- ทดสอบ path ที่มี Unicode และ path ที่ไม่มีสิทธิ์เขียน

## 7. Defect policy

- P0: คำหาย/คำผิด/คำซ้ำ/คำซ้อน — ห้าม release
- P1: สร้าง PDF ไม่ได้หรือข้อมูล config หาย — ต้องแก้ก่อน release
- P2: UI แสดงผลผิดแต่ workaround ได้ — จัดเข้า Kanban ต่อไป
