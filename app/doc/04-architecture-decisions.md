# Architecture Decision Records

## ADR-001: ใช้ PySide6

- Status: Accepted
- Decision: ใช้ PySide6 สำหรับ UI
- เหตุผล: รองรับ Windows, macOS, Linux และมี widget/ threading ที่เหมาะกับ desktop application
- ผลกระทบ: ต้องจัดการ packaging ของ Qt แยกตาม OS

## ADR-002: ใช้ SQLite + SQLAlchemy

- Status: Accepted
- Decision: เก็บคลังคำใน SQLite ผ่าน SQLAlchemy ORM
- เหตุผล: ไม่ต้องติดตั้ง database server และเหมาะกับข้อมูลคำศัพท์ระดับ local application
- ผลกระทบ: ต้องมี migration policy ผ่าน Alembic

## ADR-003: ใช้ ReportLab สร้าง PDF

- Status: Accepted
- Decision: ใช้ ReportLab และ register ฟอนท์จากไฟล์ที่ผู้ใช้เลือก
- เหตุผล: สร้าง PDF โดยตรงและควบคุมตำแหน่ง/สี/การหมุนได้ละเอียด
- ผลกระทบ: PDF ต้องฝังฟอนท์ที่รองรับภาษาไทย

## ADR-004: ตรวจ collision ด้วย rotated bounding box

- Status: Accepted for MVP
- Decision: ใช้ bounding box หลังหมุนที่ conservative
- เหตุผล: รับประกันไม่ให้คำซ้อนกันและทำงานเร็วกว่า polygon collision
- ผลกระทบ: บางกรณีพื้นที่ว่างอาจถูกใช้ได้ไม่เต็มประสิทธิภาพ
- Next review: พิจารณา polygon/SAT เมื่อรองรับ 100+ คำต่อหน้า

## ADR-005: ใช้ DOCX/TXT เป็น word-bank source และถอด PDF/OCR reader ออก

- Status: Accepted
- Decision: Reload production ใช้ adapter ที่รองรับเฉพาะ `.docx` และ `.txt`; โค้ดอ่านคำจาก PDF/OCR, diagnostic scripts, evidence OCR และ dependency เฉพาะทางถูกถอดออกจาก local scope
- เหตุผล: `.docx` อ่าน table XML ได้โดยตรง ส่วน `.txt` visual-verified อ่านได้หนึ่งคำต่อบรรทัดและตรวจนับง่ายกว่า PDF/OCR ที่มีความเสี่ยงจาก text-layer mapping, timeout และ cell evidence ที่ต้องใช้คนตรวจ
- ผลกระทบ: UI และ CLI จะเลือกหรือนำเข้าเฉพาะ DOCX/TXT เข้าฐานข้อมูล ส่วน PDF ยังเป็น output format สำหรับใบงานผ่าน ReportLab เท่านั้น
- Evidence: `app/doc/evidence/word_import_report.json`
