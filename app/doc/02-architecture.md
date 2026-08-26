# System Architecture

## 1. ภาพรวม

ระบบแบ่งเป็น 4 ชั้น:

```text
PySide6 UI
    ↓
Application Services
    ├── Table Word Source Extractor
    ├── PDF Extractor
    ├── DOCX Table Extractor
    ├── Source Contract Validator
    ├── Word Repository
    └── PDF Generator / Layout Engine
    ↓
Persistence
    ├── SQLite + SQLAlchemy
    └── TOML configuration
    ↓
Assets
    ├── Source DOCX/PDF word tables
    └── User-selectable fonts
```

## 2. โมดูลหลัก

| โมดูล | หน้าที่ |
|---|---|
| `app/ui/main_window.py` | UI แบบ 2 tab สำหรับนำเข้าข้อมูลและสร้างใบงาน, validation, progress และ worker thread |
| `app/core/extractor.py` | ตรวจเส้นตาราง, อ่านเฉพาะ word cells, แก้ลำดับ Unicode ภาษาไทย และตรวจครบทุกหน้า |
| `app/core/docx_extractor.py` | อ่านเฉพาะ cell ในตารางของไฟล์ Word `.docx` และผูกคำกับระดับชั้นจากชื่อไฟล์ |
| `app/core/word_source_extractor.py` | เลือก adapter ตามนามสกุลไฟล์และรวม source `.docx`/`.pdf` |
| `app/core/source_contract.py` | ตรวจ source contract, ระดับชั้น, cell คำ และสร้าง import report |
| `app/core/import_audit.py` | รวม audit gate สำหรับ UI/command line, สร้าง preview decision และบล็อก REVIEW/FAIL ก่อนเขียนฐานข้อมูล |
| `app/core/pdf_generator.py` | สร้างหน้า A4, วัดขนาดคำ, หมุน และจัดวาง |
| `app/db/models.py` | SQLAlchemy model ของคำศัพท์ |
| `app/db/database.py` | สร้างฐานข้อมูลและ query คำแบบสุ่ม |
| `app/core/config.py` | โหลด/บันทึก TOML configuration |
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

- `Word.grade + Word.normalized` เป็น unique key เพื่อให้คำเดียวกันอยู่คนละระดับชั้นได้
- ฐานข้อมูลใช้ `Word.grade + Word.normalized` เป็น composite primary key
- การสุ่มคำทำใน memory หลัง query จากฐานข้อมูล
- การ query รองรับตัวกรองระดับชั้น ป.1-ป.6 จาก checkbox ใน UI
- `seed = 0` หมายถึงสุ่มใหม่ทุกครั้ง
- seed อื่นใช้สำหรับทำผลลัพธ์ซ้ำได้

## 6. Table extraction contract

### DOCX word-bank contract

- แหล่งข้อมูลหลักใหม่อยู่ที่ `app/assets/words/lot1`
- อ่านเฉพาะไฟล์ `.docx` และ `.pdf`; ไฟล์ `.doc` ในโฟลเดอร์เดียวกันถูกข้าม
- อ่านเฉพาะข้อความใน table cell ที่จับคู่เลขลำดับกับคำศัพท์ได้
- ไม่อ่านข้อความหัวเรื่อง ย่อหน้า หรือคำบรรยายนอกตาราง
- ระดับชั้นอ่านจากชื่อไฟล์ เช่น `ป.1` ถึง `ป.6`
- คำซ้ำภายในระดับชั้นถูกเก็บเป็นคำไม่ซ้ำในฐานข้อมูลตาม normalized key
- `reload_words.py` และ UI ต้องผ่าน `import_audit.py` ก่อนเขียนฐานข้อมูล
- Reload ที่ผ่าน audit จะสร้าง evidence report ที่ `app/doc/evidence/word_import_report.json`
- UI รองรับการเลือกไฟล์ source เฉพาะชุด เลือกระหว่าง clear-all หรือ append และแสดง preview ก่อนยืนยันนำเข้า

### PDF legacy contract

- แหล่งข้อมูลต้องเป็น PDF ที่มี vector table และ text layer
- ชื่อไฟล์ PDF ต้องมีระดับชั้น ป.1-ป.6 หรือ P1-P6
- ใช้ `pdfplumber.find_tables()` ตรวจหา table geometry จากเส้นจริงของ PDF
- อ่าน `page.chars` เฉพาะกรอบ cell ที่เป็นคอลัมน์คำด้านซ้ายและด้านขวา
- Parser อ่านจากคู่ cell `เลขลำดับ/คำ` เป็นหลัก และใช้ fallback สำหรับ PDF legacy ที่มี geometry เก่า
- จัดอักขระตามตำแหน่ง glyph และส่งผ่าน Thai Unicode normalizer
- ช่องว่างท้ายตารางยอมรับได้สำหรับหน้าสุดท้าย แต่ห้ามมี PDF table page ที่อ่านคำไม่ได้ทั้งหมด
- `reload_words.py` เรียก `WordRepository.replace_words()` ซึ่งทำ `DELETE` แบบเทียบเท่า TRUNCATE ใน SQLite และ INSERT ภายใน transaction เดียวกัน

## 7. Source code maintainability rule

ไฟล์ source code แต่ละไฟล์ต้องไม่เกิน 700 บรรทัด โดยรวมบรรทัดว่างและ comment ด้วย หากเกินเกณฑ์ให้แยกตาม responsibility เช่น UI widgets, worker, validation, layout engine และ persistence service

## 8. Test/build friendliness

- `pyproject.toml` กำหนด `pytest` test path และ project root
- `app/__main__.py` เป็น package entry point สำหรับ `python -m app`
- `app/core/paths.py` แยก source-mode กับ PyInstaller frozen-mode
- `mt_choose_words.spec` รวม `config.toml`, assets และ fonts ลง executable
- build command: `.venv/Scripts/python.exe -m PyInstaller mt_choose_words.spec`

## 9. Thai dictionary validation

`app/core/thai_normalizer.py` ใช้ Thai dictionary จาก `pythainlp` เป็นหลักฐานประกอบการซ่อม Unicode ที่ PDF mapping ผิด โดยจะเปลี่ยน `า` เป็น `ำ` เฉพาะเมื่อได้ candidate ที่เป็นคำใน dictionary เพียงคำเดียว หากไม่ชัดเจนจะคงค่าเดิมและไม่เดาสุ่ม

## 10. Content import accuracy gate

Pipeline ห้าม import ข้อมูลที่ไม่ผ่าน source contract หากตรวจพบ source ผิดรูปแบบ ต้องหยุดและแจ้งปัญหาแทนการเก็บคำที่อาจผิดลงฐานข้อมูล

DOCX เป็น production path หลักสำหรับความถูกต้องของคำ เพราะอ่านจาก XML table โดยตรง ส่วน PDF เป็น legacy supported path ที่ใช้ได้เมื่อ text layer และ table geometry ถูกต้องตาม contract เท่านั้น

UI ไม่ทำ auto-reload ตอนเปิดโปรแกรม แต่แสดงจำนวนคำในคลังปัจจุบันแทน การเขียนฐานข้อมูลจะเกิดเฉพาะเมื่อผู้ใช้กด Reload และยืนยัน preview หลัง audit ผ่านแล้ว

หน้าจอหลักแยก workflow เป็น tab `นำเข้าข้อมูล` สำหรับ source/audit/reload และ tab `สร้างใบงาน` สำหรับ grade filter, layout settings และ export PDF เพื่อลดความสับสนและลดโอกาสกดผิดขั้นตอน
