# Feature Recommendations

## 1. Content safety and accuracy

- Source file picker: ให้ผู้ใช้เลือก `.docx`/`.txt` เฉพาะไฟล์ที่ต้องการ reload และแสดง path ของ journal หลังอ่านเสร็จ
- Import mode: เลือกได้ระหว่าง clear-all และ append
- Import preview: แสดงจำนวนคำแยกตามระดับชั้นก่อนบันทึกลงฐานข้อมูล
- Issue report: แสดงคำ/หน้า/ไฟล์ที่ไม่ผ่าน contract เพื่อส่งกลับไปแก้ source
- AI review queue: นำคำที่ Python สงสัยจาก audit report มาให้ AI/ครูตรวจทีละรายการ
- Human review status: เพิ่มสถานะ `verified` สำหรับชุดคำที่ครูตรวจแล้ว

## 2. Teacher workflow

- Word bank manager: ค้นหา แก้ไข ปิดใช้งาน หรือย้ายระดับชั้นของคำได้จาก UI
- Duplicate review: แสดงคำซ้ำในระดับเดียวกันและคำที่ซ้ำข้ามระดับชั้น
- Source history: บันทึกว่าฐานข้อมูลรอบล่าสุดมาจากไฟล์ไหน เมื่อไร และจำนวนเท่าไร
- Export word list: ส่งออกคลังคำเป็น CSV/XLSX เพื่อให้ครูตรวจทาน

## 3. Worksheet generation

- Grade-aware title template: เช่น `คำพื้นฐาน ป.{grades}`
- Difficulty filters: เลือกคำตามความยาว จำนวนพยางค์ หรือหมวดคำ
- Exclusion list: กันคำที่ไม่ต้องการใช้ในรอบนั้น
- Saved presets: เก็บชุดตั้งค่า เช่น ป.1 แบบง่าย, ป.4 แบบท้าทาย

## 4. Quality assurance

- Import checksum: บันทึก hash ของ source file เพื่อรู้ว่าไฟล์เปลี่ยนหรือไม่
- Regression fixtures: เก็บ source sample ที่ผ่านแล้วไว้ทดสอบ parser ทุกครั้ง
- Build health page: หน้าสรุปสถานะ tests, import evidence และจำนวนคำต่อชั้น

## 5. Release readiness

Feature ที่ควรทำถัดไปเป็นลำดับแรก:

1. Import preview ก่อน commit ลงฐานข้อมูล
2. Issue report แบบเปิดจาก UI ได้
3. Word bank manager สำหรับครูตรวจ/แก้คำ
4. Source checksum และ reload history
5. AI-assisted review queue สำหรับคำที่ audit mark เป็น REVIEW
