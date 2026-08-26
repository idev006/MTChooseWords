# Kanban Agile Board

## WIP Policy

- Backlog: ไม่จำกัด
- Ready: ไม่เกิน 5 งาน
- In Progress: ไม่เกิน 2 งาน
- Review/Test: ไม่เกิน 2 งาน
- Done: งานที่ผ่าน Acceptance Criteria และอัปเดตเอกสารแล้ว

## Board ปัจจุบัน

### Done

- [x] สร้างโครงสร้างโปรเจกต์ Python 3.12
- [x] ติดตั้ง PySide6, SQLAlchemy, Alembic, ReportLab, pypdf, Pillow, fonttools, tomlkit
- [x] สกัดคำจาก PDF และจัดเก็บใน SQLite
- [x] สกัดคำจากเซลล์ตารางทุกหน้าและแก้ลำดับวรรณยุกต์ภาษาไทย
- [x] เพิ่ม Reload ที่ล้างคลังคำเดิมก่อน import ใหม่
- [x] สร้าง UI ภาษาไทย
- [x] สร้าง PDF A4 แนวตั้ง/แนวนอน
- [x] ตรวจจำนวนคำก่อนสร้าง
- [x] ป้องกันคำซ้อนและกันพื้นที่ Title
- [x] สุ่มสี ขนาด และองศา
- [x] บันทึกค่าตั้งค่า TOML
- [x] เพิ่มตัวอ่าน `.docx` ที่อ่านเฉพาะคำในตารางจาก `lot1`
- [x] เพิ่ม checkbox เลือกคำศัพท์หลายระดับชั้น ป.1-ป.6
- [x] ปรับฐานข้อมูลและ query ให้กรองคำตามระดับชั้น
- [x] เพิ่มการเลือกไฟล์ source และโหมด clear-all/append
- [x] ปรับ primary key ของคำศัพท์เป็นระดับชั้น + คำ
- [x] เพิ่ม import audit gate กลางสำหรับ UI/command line
- [x] เพิ่ม import preview ใน UI ก่อนเขียนฐานข้อมูล
- [x] แยกหน้าจอเป็น tab นำเข้าข้อมูลและ tab สร้างใบงาน

### In Progress

- [ ] ทดสอบ layout กับจำนวนคำสูง เช่น 100 คำต่อหน้า
- [ ] ตรวจสอบ PDF output ด้วย visual regression

### Ready

- [ ] เพิ่ม preview ก่อน export
- [ ] เพิ่ม color palette editor ใน UI
- [ ] เพิ่มปุ่มเปิดโฟลเดอร์ output
- [ ] เพิ่มระบบ issue report UI แบบเปิดดูรายการ REVIEW รายคำได้
- [ ] เพิ่ม visual diff/review สำหรับ PDF source ที่ text layer ไม่น่าเชื่อถือ
- [ ] เพิ่ม migration revision แรกของ Alembic

### Backlog

- [ ] รองรับ OCR สำหรับ PDF สแกน
- [ ] เพิ่ม theme/layout presets
- [ ] เพิ่ม installer Windows/macOS/Linux
- [ ] เพิ่ม automated CI matrix ทั้งสามระบบ
- [ ] เพิ่ม export filename template

## Definition of Done

- โค้ดผ่าน syntax check และ automated tests
- source code ทุกไฟล์มีไม่เกิน 700 บรรทัด
- มี error handling สำหรับ input ที่ผิด
- ไม่เกิดคำซ้ำในเอกสารเดียวกัน
- ตรวจไม่พบการซ้อนกันของ bounding boxes
- มีเอกสารหรือ ADR เมื่อพฤติกรรมเปลี่ยน
