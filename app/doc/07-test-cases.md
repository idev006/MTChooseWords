# Test Cases และ Test Report

## 1. Test strategy

ใช้การทดสอบ 4 ระดับ:

1. Unit test: config, repository, layout geometry และ adapter contracts
2. Integration test: อ่าน PDF จริงและตรวจจำนวน/ลำดับคำทุกหน้า
3. Export test: สร้าง PDF จริงและตรวจจำนวนหน้า/ไฟล์
4. Build smoke test: สร้าง executable ด้วย PyInstaller

## 2. Test cases

| ID | ระดับ | กรณีทดสอบ | Expected result |
|---|---|---|---|
| TC-001 | Unit | บันทึกและโหลด TOML | ค่า config กลับมาตรงกัน |
| TC-002 | Unit | insert คำซ้ำ | เหลือคำ unique เท่านั้น |
| TC-003 | Unit | reload repository | ข้อมูลเก่าถูกแทนที่ด้วยชุดใหม่ |
| TC-004 | Unit | ตรวจ adapter contracts | extractor/exporter/repository มี method ตาม contract |
| TC-005 | Unit | จัดวางคำหลายคำ | ได้จำนวนคำตามต้องการ |
| TC-006 | Unit | ตรวจ bounding boxes | ไม่มีคู่ใด intersect กัน |
| TC-007 | Integration | อ่านตาราง PDF จริง | พบ 41 ตารางหน้า รวม 1,210 คำ |
| TC-008 | Integration | ตรวจคำหน้าแรก | เริ่มด้วย กัน, กระบุง, กระจง, กระมัง |
| TC-009 | Integration | ตรวจหน้าสุดท้าย | มีคำ 10 คำและไม่มี cell ว่างปะปนในชุดคำที่ได้ |
| TC-010 | Export | สร้าง PDF 2 หน้า | PDF มี 2 หน้าและมีขนาดไฟล์มากกว่า 0 |
| TC-011 | Build | PyInstaller spec | สร้าง `dist/MTChooseWords.exe` สำเร็จ |
| TC-012 | Regression | `ตาลึง` จาก PDF ที่ mapping ผิด | ได้ `ตำลึง` |
| TC-013 | Regression | `กานัน` จาก PDF ที่ mapping ผิด | ได้ `กำนัน` |
| TC-014 | Unit | DOCX มีข้อความนอกตารางและตารางคำ | อ่านเฉพาะ cell คำในตาราง |
| TC-015 | Unit | คำเดียวกันอยู่คนละระดับชั้น | เก็บและกรองตามระดับชั้นได้ |
| TC-016 | Unit | Source ไม่มีระดับชั้นในชื่อไฟล์ | Import ล้มเหลวแบบ fail-closed |
| TC-017 | Unit | โฟลเดอร์มี `.docx` และ `.doc` | อ่าน `.docx` และไม่อ่าน `.doc` |
| TC-018 | Evidence | Reload source จริง | สร้าง `word_import_report.json` พร้อม counts/source files |
| TC-019 | Unit | Append import | เพิ่มคำใหม่โดยไม่ล้างคำเดิมและไม่เพิ่ม duplicate key |
| TC-020 | Unit | Corrupt text layer character | Source contract ปฏิเสธอักขระผิดปกติ |
| TC-021 | Unit | Long wrapped word cell | อ่านได้และ mark เป็น `long_cell_review` |

## 3. Test result — 2026-07-26

คำสั่ง:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m pytest -q
```

ผลลัพธ์:

```text
28 passed in 62.76s
```

ครอบคลุม TC-001 ถึง TC-018 ใน automated tests และ reload evidence

คำสั่ง build:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m PyInstaller --noconfirm mt_choose_words.spec
```

ผลลัพธ์: **ผ่าน** — สร้าง `dist/MTChooseWords.exe` สำเร็จ

## 4. Manual test cases ที่ยังต้องทำบน OS อื่น

- เปิด UI บน macOS และ Linux
- เลือกฟอนท์ผ่าน dialog
- กด Reload จาก UI และตรวจ status/progress
- สร้าง PDF แนวตั้งและแนวนอน
- เปิด PDF ด้วย viewer ของแต่ละ OS
- ทดสอบ path ที่มี Unicode และ path ที่ไม่มีสิทธิ์เขียน

## 5. Defect policy

- P0: คำหาย/คำผิด/คำซ้ำ/คำซ้อน — ห้าม release
- P1: สร้าง PDF ไม่ได้หรือข้อมูล config หาย — ต้องแก้ก่อน release
- P2: UI แสดงผลผิดแต่ workaround ได้ — จัดเข้า Kanban ต่อไป
