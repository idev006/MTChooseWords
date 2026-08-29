# Test Plan และ Acceptance Criteria

## 1. Functional Tests

| Test | กรณีทดสอบ | ผลที่คาดหวัง |
|---|---|---|
| T-01 | Production import DOCX/TXT | ได้คำจาก `.docx`/`.txt` และบันทึก SQLite สำเร็จ |
| T-01A | ตรวจ DOCX table cells | อ่านเฉพาะ cell คำในตารางและไม่อ่านข้อความนอกตาราง |
| T-01B | Reload ซ้ำ | คลังคำเดิมถูกล้างก่อน import และจำนวนไม่เพิ่มซ้ำ |
| T-01C | สกัด DOCX เฉพาะตาราง | ข้อความนอกตารางไม่ถูก import และ cell คำในตารางถูกอ่านพร้อมระดับชั้น |
| T-01D | เลือกระดับชั้น | count และ random words ใช้เฉพาะระดับชั้นที่เลือก |
| T-01E | Source contract | ไฟล์ที่ไม่มีระดับชั้นหรือไม่มีตารางคำต้อง import ไม่สำเร็จ |
| T-01F | Import evidence | Reload สำเร็จแล้วต้องสร้างรายงานจำนวน cell, unique words, duplicates และ source files |
| T-01G | Append mode | Import เพิ่มโดยไม่ล้างฐานข้อมูลเดิม และไม่เพิ่มคำซ้ำในระดับชั้นเดิม |
| T-01H | Long cell review | คำยาวใน cell เดียวต้องอ่านได้และถูก mark ให้ review แทนการตัดทิ้ง |
| T-01I | Import audit gate | Reload ต้องถูกบล็อกเมื่อมี REVIEW/FAIL และผ่านได้เฉพาะรายการที่ตรวจรับแล้ว |
| T-01J | Import preview | UI ต้องแสดง preview และต้องได้รับการยืนยันก่อนเขียน database |
| T-01K | Non-blocking import UI | การ audit/reload ต้องทำใน worker thread และรายงาน progress/status ให้ผู้ใช้เห็น |
| T-01L | Pluggable source adapters | Table source extractor ต้องรับ adapter registry ที่ inject ได้เพื่อให้ทดสอบ/เพิ่ม parser ใหม่ได้ง่าย |
| T-01M | PDF reader removed | ไม่มี adapter, script หรือ dependency สำหรับอ่านคำจาก PDF/OCR ใน local code |
| T-01N | Unsupported PDF source | default importer และ UI/CLI reload ต้องไม่รับ PDF เข้า database |
| T-01O | TXT source import | อ่าน `.txt` แบบหนึ่งคำต่อบรรทัด ระดับชั้นจากชื่อไฟล์ และใช้เลขบรรทัดเป็น source index |
| T-01P | Import journal | audit/reload ต้องสร้าง `mtchoosewords_import_journal.json` ในโฟลเดอร์ source ทุกครั้ง |
| T-01Q | Canonical grade-word key | ฐานข้อมูลต้องเก็บระดับชั้นเป็น `ป.1`-`ป.6`, trim คำก่อนบันทึก และกันซ้ำด้วย `ป.x + normalized word` |
| T-01R | Combined source duplicate audit | เมื่อ audit DOCX+TXT พร้อมกัน ต้องนับ duplicate ข้าม source ในระดับเดียวกันได้ถูกต้อง |
| T-01S | Separate clear/import buttons | UI ต้องแยกปุ่มล้างข้อมูลคำออกจากปุ่มนำเข้ารายการคำ และ worker ของแต่ละปุ่มต้องไม่ทำงานปนกัน |
| T-01T | Portable path manager | Config, reports, journals และ database source_file ต้องใช้ relative path เมื่ออยู่ใต้ project root |
| T-02 | ขอคำมากกว่าคลัง | แจ้งเตือนและไม่สร้าง PDF |
| T-03 | หลายหน้า | คำไม่ซ้ำกันข้ามทุกหน้า |
| T-04 | เปลี่ยน orientation | ได้ A4 portrait/landscape ถูกต้อง |
| T-05 | ตั้ง font range | ทุกคำอยู่ภายใน minimum/maximum |
| T-06 | หมุนคำ | องศาอยู่ในช่วงที่กำหนด |
| T-07 | Title | อยู่กึ่งกลางด้านบนและไม่ถูกคำทับ |
| T-08 | บันทึก config | ปิด/เปิดโปรแกรมแล้วค่ากลับมาเหมือนเดิม |

## 2. Property Checks

- จำนวนคำใน output = จำนวนหน้าคูณจำนวนคำต่อหน้า
- `len(words) == len(set(words_normalized))`
- bounding box ทุกคู่ต้องไม่ intersect
- bounding box ทุกอันอยู่ใน safe area
- PDF มีจำนวนหน้าเท่ากับค่าที่ผู้ใช้ระบุ
- Reload สำเร็จแล้ว `count(words)` เท่ากับจำนวนคำ unique ที่สกัดได้
- เมื่อเลือกหลายระดับชั้น `count(words)` ต้องนับเฉพาะชั้นที่เลือก
- Source ทุกไฟล์ที่ใช้ต้องมี grade อยู่ในชื่อไฟล์
- Import report ต้องระบุ source files ที่ถูกใช้จริง
- ฐานข้อมูลต้องใช้ `ป.x + normalized` เป็น key และ append mode ต้องไม่สร้าง duplicate key
- คำต้องถูก trim หัวท้ายและ normalize ช่องว่างก่อนสร้าง key
- คำยาวผิดปกติควรถูก audit เพื่อ review ก่อน production import
- UI และ command line ต้องใช้ audit gate เดียวกันก่อนเขียนฐานข้อมูล
- งาน audit/import/clear ใน UI ต้องไม่ทำบน main thread
- Source extractor ต้องไม่ hard-code parser จนทดสอบด้วย adapter จำลองไม่ได้
- ไม่เหลือ dependency หรือ adapter สำหรับอ่านคำจาก PDF/OCR
- ไม่มี absolute project path เช่น `F:\...` หรือ `C:\...` ใน config/evidence/database ที่นำขึ้น git

## 3. Cross-platform Matrix

| OS | Python | UI launch | PDF export | Font embedding |
|---|---|---|---|---|
| Windows | 3.12 | ต้องผ่าน | ต้องผ่าน | ต้องผ่าน |
| macOS | 3.12 | ต้องผ่าน | ต้องผ่าน | ต้องผ่าน |
| Linux | 3.12 | ต้องผ่าน | ต้องผ่าน | ต้องผ่าน |

## 4. Performance Targets

- UI ไม่ค้างระหว่างสร้าง PDF
- การสร้าง 1 หน้า 30 คำเสร็จในระดับไม่กี่วินาทีบนเครื่องทั่วไป
- หากจัดวางไม่ได้ ต้องจบด้วยข้อความผิดพลาดที่ระบุคำลำดับใด
- layout ต้องรองรับ baseline 30 คำต่อหน้า ด้วยฟอนท์โครงการและช่วง 20–60 pt

## 5. Maintainability Check

- ตรวจนับทุกไฟล์ `.py` ใน `app/`, `scripts/` และ `alembic/`
- ต้องไม่พบไฟล์ที่มีจำนวนบรรทัดมากกว่า 700

## 6. Automated test/build commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mt_choose_words.spec
```

Baseline ล่าสุด: pytest ผ่าน 49 tests, audit DOCX+TXT ผ่าน 12 ไฟล์โดยไม่มี REVIEW/FAIL, อ่านได้ 14,374 cells, เหลือ 8,705 unique words, duplicate 5,669 cells ตามคีย์ `ป.x + normalized word`, committed SQLite database มี 8,705 คำ, ไม่มี trim violation และไม่มี absolute source path
