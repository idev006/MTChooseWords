# คู่มือผู้ใช้

## ติดตั้ง dependency

ใช้ Python ใน virtual environment ของโครงการเท่านั้น:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

หากเครื่องพัฒนาเคยติดตั้ง library สำหรับอ่านคำจาก PDF/OCR ไว้ สามารถล้างออกด้วย batch file นี้:

```text
Cleanup_Unused_PDF_OCR_Libs.bat
```

batch file นี้ใช้เฉพาะ `.venv` ของโครงการ และจะถามยืนยันก่อนถอน library

## เริ่มโปรแกรม

วิธีที่ง่ายที่สุดบน Windows คือดับเบิลคลิกไฟล์:

```text
MTChooseWords.bat
```

จากเมนูสามารถเปิดโปรแกรม, นำเข้าคำจาก DOCX/TXT, รัน tests หรือ Build EXE ได้

```powershell
.\.venv\Scripts\python.exe -m app.main
```

หรือใช้ package entry point:

```powershell
.\.venv\Scripts\python.exe -m app
```

## Build executable

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mt_choose_words.spec
```

ผลลัพธ์อยู่ที่ `dist/MTChooseWords.exe` บน Windows โดย source เดียวกันสามารถ build บน macOS/Linux ด้วย PyInstaller ของระบบนั้น

## ขั้นตอนใช้งาน

หน้าจอหลักแบ่งเป็น 2 tab ตามงาน:

- `นำเข้าข้อมูล`: เลือกไฟล์คำศัพท์, ล้างข้อมูลคำในฐานข้อมูล และนำเข้ารายการคำ
- `สร้างใบงาน`: เลือกระดับชั้น ตั้งค่าหน้าเอกสาร และสร้าง PDF

1. ใส่ไฟล์คำศัพท์ `.docx` ที่เป็นตารางใน `app/assets/words/lot1` หรือ `.txt` แบบหนึ่งคำต่อบรรทัดใน `app/assets/words/text`
2. ใส่ฟอนท์ที่รองรับภาษาไทยใน `app/assets/fonts`
3. ตั้งชื่อไฟล์ให้มีระดับชั้น เช่น `ป.1`, `ป.2` หรือ `P3`
4. ที่ tab `นำเข้าข้อมูล` เลือกไฟล์คำศัพท์เฉพาะชุด หรือปล่อยค่าเริ่มต้นเพื่อใช้ทั้งโฟลเดอร์
5. ถ้าต้องการเริ่มฐานข้อมูลใหม่ ให้กด “ล้างข้อมูลคำในฐานข้อมูล” และยืนยัน
6. กด “นำเข้ารายการคำ” ระบบจะตรวจ source ก่อน หากผ่านจะแสดง preview ให้ยืนยัน
7. ยืนยัน preview เพื่อให้ระบบนำคำเข้า database หรือยกเลิกหากจำนวนไม่ตรงกับที่คาด
8. การนำเข้ารายการคำจะเพิ่มคำโดยไม่ล้างข้อมูลเดิม หากพบคำซ้ำระดับเดียวกันจะเก็บเพียงหนึ่งคำตาม key `ป.x + คำ`
9. ไปที่ tab `สร้างใบงาน`
10. เลือก checkbox ระดับชั้น ป.1-ป.6 ที่ต้องการใช้
11. กำหนดจำนวนหน้าและจำนวนคำต่อหน้า
12. เลือกฟอนท์, orientation, ขนาดฟอนท์ และองศา
13. กำหนด Title และค่าการแสดงผล
14. กด “บันทึกการตั้งค่า” หากต้องการใช้ค่าเดิมครั้งถัดไป
15. กด “สร้าง PDF”

ระหว่างนำเข้าคำ, ล้างข้อมูลคำ และสร้าง PDF โปรแกรมจะแสดง progress bar และข้อความสถานะด้านล่าง หน้าจอหลักยังตอบสนองได้ ไม่ควรเกิดอาการเหมือนโปรแกรมค้าง

กำหนดจำนวนชุดเอกสารได้จากช่อง `จำนวนชุดเอกสาร` ระบบจะสุ่มคำไม่ซ้ำภายใน PDF แต่ละไฟล์ ส่วน PDF คนละไฟล์สามารถมีคำซ้ำกันได้ แล้วสร้างไฟล์แยก เช่น `mt_choose_words-set01-100-20260726-153045.pdf` และ `mt_choose_words-set02-100-20260726-153046.pdf`

## Title box settings

The Title section supports three additional settings in the UI and `config.toml`:

- `title_margin_bottom_px`: extra space below the Title before the word layout begins.
- `title_padding_px`: inner space between the Title text and its background.
- `title_bgcolor`: background color of the Title box, for example `#FFF8E1`.

The word placement reserves all three values, so words do not overlap the Title box.

## Reload ผ่าน command line

```powershell
.\.venv\Scripts\python.exe scripts\reload_words.py
```

คำสั่งนี้จะรัน audit gate ก่อนเสมอ หาก source มีสถานะ REVIEW หรือ FAIL ระบบจะหยุดก่อนเขียน database และให้ตรวจรายงานก่อน ค่าเริ่มต้นของ command line ยังเป็น clear-all เพื่อเหมาะกับงาน build/certification ส่วน UI แยกปุ่มล้างข้อมูลออกจากปุ่มนำเข้าเพื่อลดความสับสนของผู้ใช้

หลัง reload สำเร็จ ระบบสร้างรายงานตรวจรับที่:

```text
app/doc/evidence/word_import_report.json
```

ทุกครั้งที่อ่าน source ระบบจะสร้าง journal ในโฟลเดอร์ source เช่น:

```text
app/assets/words/text/mtchoosewords_import_journal.json
```

รายงาน audit ก่อน import อยู่ที่:

```text
app/doc/evidence/word_source_audit_report.json
```

โปรแกรมไม่มีคำสั่งอ่านคำจาก PDF/OCR แล้ว หาก source เป็น PDF ให้แปลงหรือจัดทำเป็น `.docx`/`.txt` ที่ตรวจรับได้ก่อนนำเข้า

## ข้อจำกัดปัจจุบัน

- โปรแกรมไม่อ่านคำจาก PDF/OCR
- ไฟล์ `.doc` ไม่ถูกอ่านโดยตรง ต้องแปลงเป็น `.docx` ก่อน
- หากจำนวนคำมากเกินพื้นที่แม้ลดถึง minimum แล้ว ระบบจะแจ้งเตือนแทนการสร้างไฟล์ที่คำซ้อนกัน
- ฟอนท์ที่เลือกต้องรองรับ glyph ของภาษาไทย
