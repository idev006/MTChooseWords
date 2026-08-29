# System Architecture

## 1. ภาพรวม

ระบบแบ่งเป็น 4 ชั้น:

```text
PySide6 UI
    ↓
Application Services
    ├── Table Word Source Extractor
    ├── DOCX Table Extractor
    ├── TXT Line Extractor
    ├── Source Contract Validator
    ├── Word Repository
    └── PDF Generator / Layout Engine
    ↓
Persistence
    ├── SQLite + SQLAlchemy
    └── TOML configuration
    ↓
Assets
    ├── Source DOCX/TXT word tables
    └── User-selectable fonts
```

## 2. โมดูลหลัก

| โมดูล | หน้าที่ |
|---|---|
| `app/ui/main_window.py` | UI แบบ 2 tab สำหรับนำเข้าข้อมูลและสร้างใบงาน, validation, ปุ่มล้างข้อมูล/นำเข้าที่แยกกัน, progress และ worker thread |
| `app/core/docx_extractor.py` | อ่านเฉพาะ cell ในตารางของไฟล์ Word `.docx` และผูกคำกับระดับชั้นจากชื่อไฟล์ |
| `app/core/text_extractor.py` | อ่านไฟล์ `.txt` แบบหนึ่งคำต่อหนึ่งบรรทัดและผูกคำกับระดับชั้นจากชื่อไฟล์ |
| `app/core/source_adapters.py` | registry ของ source adapters โดยเปิดเฉพาะ DOCX/TXT สำหรับการนำเข้าคำ |
| `app/core/word_source_extractor.py` | เลือก adapter production ตามนามสกุลไฟล์และรวม source `.docx`/`.txt` |
| `app/core/source_contract.py` | ตรวจ source contract, ระดับชั้น, cell คำ และสร้าง import report |
| `app/core/import_audit.py` | รวม audit gate สำหรับ UI/command line, สร้าง preview decision และบล็อก REVIEW/FAIL ก่อนเขียนฐานข้อมูล |
| `app/core/pdf_generator.py` | สร้างหน้า A4, วัดขนาดคำ, หมุน และจัดวาง |
| `app/db/models.py` | SQLAlchemy model ของคำศัพท์ |
| `app/db/database.py` | สร้างฐานข้อมูลและ query คำแบบสุ่ม |
| `app/core/config.py` | โหลด/บันทึก TOML configuration |
| `app/core/paths.py` | จัดการ application root, resolve relative paths และแปลง path ใต้ project root กลับเป็น relative path สำหรับ config/evidence |
| `alembic/` | Database migration |

## 3. กติกาการจัดวาง

1. เลือกคำแบบไม่ซ้ำให้ครบทุกหน้าก่อนเริ่มสร้าง PDF
2. สุ่มขนาดและองศาของคำ
3. สร้าง conservative rotated bounding box
4. สุ่มตำแหน่งภายใน safe area ของหน้า
5. ตรวจขอบกระดาษและการชนกับคำเดิม
6. หากวางไม่ได้ให้ลดขนาดคำจนถึง minimum
7. หากยังวางไม่ได้ให้หยุดและแจ้งผู้ใช้

การใช้ bounding box ที่เผื่อพื้นที่มากกว่ารูปร่างจริงช่วยรับประกันว่าไม่มีการซ้อนกัน แม้จะอนุรักษ์นิยมกว่าการตรวจ polygon จริง

## 4. การแปลงหน่วย

PDF ใช้ point ส่วนระยะห่าง Title รับเป็น pixel ตาม requirement:

`1 px = 0.75 pt` โดยอิง 96 DPI

## 5. ความถูกต้องของข้อมูล

- `Word.grade + Word.normalized` เป็น unique key เพื่อให้คำเดียวกันอยู่คนละระดับชั้นได้ โดย `Word.grade` เก็บเป็นข้อความ `ป.1` ถึง `ป.6`
- ฐานข้อมูลใช้ `Word.grade + Word.normalized` เป็น composite primary key และ trim/collapse ช่องว่างของคำก่อนสร้าง `normalized`
- การสุ่มคำทำใน memory หลัง query จากฐานข้อมูล
- การ query รองรับตัวกรองระดับชั้น ป.1-ป.6 จาก checkbox ใน UI
- `seed = 0` หมายถึงสุ่มใหม่ทุกครั้ง
- seed อื่นใช้สำหรับทำผลลัพธ์ซ้ำได้

## 6. Table extraction contract

### DOCX/TXT word-bank contract

- แหล่งข้อมูลหลักใหม่อยู่ที่ `app/assets/words/lot1`
- แหล่งข้อมูล text verified อยู่ที่ `app/assets/words/text`
- อ่านเฉพาะไฟล์ `.docx` และ `.txt`; ไฟล์ `.doc` และ `.pdf` ในโฟลเดอร์เดียวกันถูกข้าม
- อ่านเฉพาะข้อความใน table cell ที่จับคู่เลขลำดับกับคำศัพท์ได้
- สำหรับ `.txt` อ่านหนึ่งคำต่อหนึ่งบรรทัด และใช้เลขบรรทัดเป็น source index
- ไม่อ่านข้อความหัวเรื่อง ย่อหน้า หรือคำบรรยายนอกตาราง
- ระดับชั้นอ่านจากชื่อไฟล์ เช่น `ป.1` ถึง `ป.6`
- ตัวอย่างชื่อไฟล์ text: `คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt` หมายถึง ป.1
- คำซ้ำภายในระดับชั้นและคำซ้ำข้าม source DOCX/TXT ถูกเก็บเป็นคำไม่ซ้ำในฐานข้อมูลตามคีย์ `ป.x + normalized`
- `reload_words.py` และ UI ต้องผ่าน `import_audit.py` ก่อนเขียนฐานข้อมูล
- Reload ที่ผ่าน audit จะสร้าง evidence report ที่ `app/doc/evidence/word_import_report.json`
- ทุกครั้งที่ audit อ่าน source จะสร้าง `mtchoosewords_import_journal.json` ในโฟลเดอร์ที่อ่าน เพื่อบันทึก source, summary, PASS/REVIEW/FAIL และ error
- UI รองรับการเลือกไฟล์ source เฉพาะชุด, ปุ่มล้างข้อมูลคำในฐานข้อมูลที่แยกจากปุ่มนำเข้ารายการคำ และแสดง preview ก่อนยืนยันนำเข้า

### Removed PDF/OCR word reader

- ไม่มี production หรือ diagnostic adapter สำหรับอ่านคำจาก PDF/OCR ใน local code
- ไม่มี dependency เฉพาะทางของ PDF/OCR reader เช่น `pdfplumber`, `pymupdf`, `pytesseract`, `pythainlp`
- PDF ยังเป็น output format สำหรับสร้างใบงานผ่าน `app/core/pdf_generator.py`

## 7. Source code maintainability rule

ไฟล์ source code แต่ละไฟล์ต้องไม่เกิน 700 บรรทัด โดยรวมบรรทัดว่างและ comment ด้วย หากเกินเกณฑ์ให้แยกตาม responsibility เช่น UI widgets, worker, validation, layout engine และ persistence service

## 8. Test/build friendliness

- `pyproject.toml` กำหนด `pytest` test path และ project root
- `app/__main__.py` เป็น package entry point สำหรับ `python -m app`
- `app/core/paths.py` แยก source-mode กับ PyInstaller frozen-mode และเป็น path manager กลางสำหรับ config, source, database, output และ evidence
- `mt_choose_words.spec` รวม `config.toml`, assets และ fonts ลง executable
- build command: `.venv/Scripts/python.exe -m PyInstaller mt_choose_words.spec`

## 8.1 Portable path policy

- ค่าที่บันทึกใน `config.toml`, import journal, audit report, import report และ SQLite `source_file` ต้องเป็น relative path เมื่ออยู่ภายใน project/application root
- โค้ด application และ scripts ต้อง resolve path ผ่าน `PathManager` แทนการอิง current working directory
- Absolute path ใช้ได้เฉพาะกรณีผู้ใช้เลือก path ภายนอก project root เช่น output folder นอกโฟลเดอร์โปรแกรม

## 9. Thai text normalization

`app/core/thai_normalizer.py` ทำ normalization แบบไม่เดาคำ โดย trim ขอบคำ, normalize Unicode เป็น NFC และซ่อมลำดับ `นิคหิต + า` ให้เป็น `ำ` เฉพาะกรณีที่ source เก็บ glyph แบบแยกตัวอักษร ไม่ใช้ dictionary เพื่อเดาสะกดคำ

## 10. Content import accuracy gate

Pipeline ห้าม import ข้อมูลที่ไม่ผ่าน source contract หากตรวจพบ source ผิดรูปแบบ ต้องหยุดและแจ้งปัญหาแทนการเก็บคำที่อาจผิดลงฐานข้อมูล

DOCX และ TXT เป็น production path สำหรับความถูกต้องของคำ เพราะอ่านจากโครงสร้างที่ตรวจรับได้โดยตรง ส่วน PDF/OCR reader ถูกถอดออกเพื่อป้องกันคำที่ยังไม่น่าเชื่อถือเข้าสู่ฐานข้อมูล

UI ไม่ทำ auto-reload ตอนเปิดโปรแกรม แต่แสดงจำนวนคำในคลังปัจจุบันแทน การเขียนฐานข้อมูลจะเกิดเฉพาะเมื่อผู้ใช้กด “นำเข้ารายการคำ” และยืนยัน preview หลัง audit ผ่านแล้ว

การล้างฐานข้อมูลเป็นคำสั่งแยกต่างหาก ผู้ใช้ต้องกด “ล้างข้อมูลคำในฐานข้อมูล” และยืนยันก่อน ระบบจึงจะล้างคำทั้งหมด โดยไม่อ่าน source หรือ import คำในขั้นตอนเดียวกัน

หน้าจอหลักแยก workflow เป็น tab `นำเข้าข้อมูล` สำหรับ source/audit/reload และ tab `สร้างใบงาน` สำหรับ grade filter, layout settings และ export PDF เพื่อลดความสับสนและลดโอกาสกดผิดขั้นตอน

งานที่ใช้เวลานานต้องทำผ่าน worker thread ได้แก่ audit/import คำศัพท์, clear database และ export PDF เพื่อให้หน้าจอยังตอบสนองระหว่างประมวลผล ผู้ใช้จะเห็น progress bar และข้อความสถานะของขั้นตอนปัจจุบัน
