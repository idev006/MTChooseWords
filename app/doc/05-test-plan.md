# Test Plan และ Acceptance Criteria

## 1. Functional Tests

| Test | กรณีทดสอบ | ผลที่คาดหวัง |
|---|---|---|
| T-01 | สกัด PDF text-based | ได้คำและบันทึก SQLite สำเร็จ |
| T-01A | ตรวจ table cells | PDF ปัจจุบันได้ 41 ตารางหน้าและ 1,210 เซลล์คำ |
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
| T-02 | PDF ไม่มี text layer | แจ้งปัญหา ไม่สร้างผลลัพธ์ผิดพลาดเงียบ ๆ |
| T-03 | ขอคำมากกว่าคลัง | แจ้งเตือนและไม่สร้าง PDF |
| T-04 | หลายหน้า | คำไม่ซ้ำกันข้ามทุกหน้า |
| T-05 | เปลี่ยน orientation | ได้ A4 portrait/landscape ถูกต้อง |
| T-06 | ตั้ง font range | ทุกคำอยู่ภายใน minimum/maximum |
| T-07 | หมุนคำ | องศาอยู่ในช่วงที่กำหนด |
| T-08 | Title | อยู่กึ่งกลางด้านบนและไม่ถูกคำทับ |
| T-09 | บันทึก config | ปิด/เปิดโปรแกรมแล้วค่ากลับมาเหมือนเดิม |

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
- ฐานข้อมูลต้องใช้ `grade + normalized` เป็น key และ append mode ต้องไม่สร้าง duplicate key
- คำยาวผิดปกติควรถูก audit เพื่อ review ก่อน production import
- UI และ command line ต้องใช้ audit gate เดียวกันก่อนเขียนฐานข้อมูล
- งาน audit/reload ใน UI ต้องไม่ทำบน main thread
- Source extractor ต้องไม่ hard-code parser จนทดสอบด้วย adapter จำลองไม่ได้

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
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m pytest -q
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mt_choose_words.spec
```

Baseline ล่าสุด: pytest ผ่าน 33 tests, audit DOCX lot1 ผ่าน 6 ไฟล์โดยไม่มี REVIEW/FAIL และ Reload DOCX จริงสำเร็จพร้อม import evidence
