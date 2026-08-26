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

## ADR-005: ใช้ DOCX เป็น production word-bank source หลัก และคง PDF เป็น legacy adapter

- Status: Accepted
- Decision: Reload ใช้ adapter รวมที่รองรับ `.docx` และ `.pdf` แบบ table-based โดย `.docx` เป็นเส้นทางหลักสำหรับ source ชุด ป.1-ป.6
- เหตุผล: `.docx` อ่าน table XML ได้โดยตรง จึงลดความเสี่ยงจาก PDF text-layer mapping ผิด ส่วน PDF ยังจำเป็นสำหรับ backward compatibility
- ผลกระทบ: source ทุกไฟล์ต้องมีระดับชั้นในชื่อไฟล์ และ pipeline ต้องหยุดเมื่อไม่ผ่าน source contract
- Evidence: `app/doc/evidence/word_import_report.json`
