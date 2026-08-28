# คู่มือผู้ใช้

## ติดตั้ง dependency

ใช้ Python ใน virtual environment ของโครงการเท่านั้น:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## เริ่มโปรแกรม

วิธีที่ง่ายที่สุดบน Windows คือดับเบิลคลิกไฟล์:

```text
MTChooseWords.bat
```

จากเมนูสามารถเปิดโปรแกรม, Reload คำ, รัน tests หรือ Build EXE ได้

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m app.main
```

หรือใช้ package entry point:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m app
```

## Build executable

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mt_choose_words.spec
```

ผลลัพธ์อยู่ที่ `dist/MTChooseWords.exe` บน Windows โดย source เดียวกันสามารถ build บน macOS/Linux ด้วย PyInstaller ของระบบนั้น

## ขั้นตอนใช้งาน

หน้าจอหลักแบ่งเป็น 2 tab ตามงาน:

- `นำเข้าข้อมูล`: เลือกไฟล์คำศัพท์และ Reload คำเข้า database
- `สร้างใบงาน`: เลือกระดับชั้น ตั้งค่าหน้าเอกสาร และสร้าง PDF

1. ใส่ไฟล์คำศัพท์ `.docx` ที่เป็นตารางใน `app/assets/words/lot1`
2. ใส่ฟอนท์ที่รองรับภาษาไทยใน `app/assets/fonts`
3. ตั้งชื่อไฟล์ให้มีระดับชั้น เช่น `ป.1`, `ป.2` หรือ `P3`
4. ที่ tab `นำเข้าข้อมูล` เลือกไฟล์คำศัพท์เฉพาะชุด หรือปล่อยค่าเริ่มต้นเพื่อใช้ทั้งโฟลเดอร์
5. เลือกว่าจะ “ล้างคลังคำก่อน Reload” หรือ append เข้าไปโดยไม่ล้างของเดิม
6. กด “Reload คำจาก DOCX” ระบบจะตรวจ source ก่อน หากผ่านจะแสดง preview ให้ยืนยัน
7. ยืนยัน preview เพื่อให้ระบบนำคำเข้า database หรือยกเลิกหากจำนวนไม่ตรงกับที่คาด
8. ไปที่ tab `สร้างใบงาน`
9. เลือก checkbox ระดับชั้น ป.1-ป.6 ที่ต้องการใช้
10. กำหนดจำนวนหน้าและจำนวนคำต่อหน้า
11. เลือกฟอนท์, orientation, ขนาดฟอนท์ และองศา
12. กำหนด Title และค่าการแสดงผล
13. กด “บันทึกการตั้งค่า” หากต้องการใช้ค่าเดิมครั้งถัดไป
14. กด “สร้าง PDF”

ระหว่าง Reload และสร้าง PDF โปรแกรมจะแสดง progress bar และข้อความสถานะด้านล่าง หน้าจอหลักยังตอบสนองได้ ไม่ควรเกิดอาการเหมือนโปรแกรมค้าง

กำหนดจำนวนชุดเอกสารได้จากช่อง `จำนวนชุดเอกสาร` ระบบจะสุ่มคำไม่ซ้ำภายใน PDF แต่ละไฟล์ ส่วน PDF คนละไฟล์สามารถมีคำซ้ำกันได้ แล้วสร้างไฟล์แยก เช่น `mt_choose_words-set01-100-20260726-153045.pdf` และ `mt_choose_words-set02-100-20260726-153046.pdf`

## Reload ผ่าน command line

## Title box settings

The Title section supports three additional settings in the UI and `config.toml`:

- `title_margin_bottom_px`: extra space below the Title before the word layout begins.
- `title_padding_px`: inner space between the Title text and its background.
- `title_bgcolor`: background color of the Title box, for example `#FFF8E1`.

The word placement reserves all three values, so words do not overlap the Title box.

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe scripts\reload_words.py
```

คำสั่งนี้จะรัน audit gate ก่อนเสมอ หาก source มีสถานะ REVIEW หรือ FAIL ระบบจะหยุดก่อนเขียน database และให้ตรวจรายงานก่อน

หลัง reload สำเร็จ ระบบสร้างรายงานตรวจรับที่:

```text
app/doc/evidence/word_import_report.json
```

รายงาน audit ก่อน import อยู่ที่:

```text
app/doc/evidence/word_source_audit_report.json
```

PDF ถูกปิดจากการ Reload เข้า database ชั่วคราว เพราะยังไม่มีขั้นตอนตรวจรับที่ดีพอสำหรับงานการศึกษา หากต้องตรวจ PDF โดยไม่ Reload เข้า database ให้ใช้คำสั่ง diagnostic:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe scripts\diagnose_pdf_sources.py app\assets\words\pdf --start-page 1 --max-pages 12
```

หากต้องตรวจ OCR เฉพาะหน้า ให้ใช้:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe scripts\diagnose_pdf_ocr_cells.py "app\assets\words\pdf\_บัญชีคำพื้นฐาน ป๖ (สมบูรณ์).pdf" --page 10 --expected-count 15
```

หากต้องอ่าน PDF ทั้งโฟลเดอร์เพื่อสร้างคิวตรวจ โดยยังไม่ Reload เข้า database ให้ใช้:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe scripts\read_pdf_ocr_folder.py app\assets\words\pdf --start-page 10 --max-pages-per-file 1 --max-cells-per-page 80 --page-timeout-seconds 45
```

โปรแกรมจะสร้างรายงาน `app/doc/evidence/pdf_ocr_folder_read_report.json` และไฟล์ `app/doc/evidence/pdf_ocr_review_queue.csv` ให้ผู้ใช้เปิดตรวจรายการที่ยังไม่มั่นใจพร้อมหลักฐานรูป cell

## ข้อจำกัดปัจจุบัน

- PDF ทุกชนิดถูกปิดจาก production import ชั่วคราว และใช้ได้เฉพาะ diagnostic/review command
- ไฟล์ `.doc` ไม่ถูกอ่านโดยตรง ต้องแปลงเป็น `.docx` ก่อน
- ก่อนเปิด PDF import อีกครั้ง ต้องมี expected output ที่คนตรวจรับแล้ว, review queue ที่ใช้ง่าย และ approval log ที่ตรวจย้อนหลังได้
- หากจำนวนคำมากเกินพื้นที่แม้ลดถึง minimum แล้ว ระบบจะแจ้งเตือนแทนการสร้างไฟล์ที่คำซ้อนกัน
- ฟอนท์ที่เลือกต้องรองรับ glyph ของภาษาไทย
