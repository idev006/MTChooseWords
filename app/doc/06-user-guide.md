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

1. ใส่ไฟล์คำศัพท์ `.docx` หรือ `.pdf` ที่เป็นตารางใน `app/assets/words/lot1`
2. ใส่ฟอนท์ที่รองรับภาษาไทยใน `app/assets/fonts`
3. ตั้งชื่อไฟล์ให้มีระดับชั้น เช่น `ป.1`, `ป.2` หรือ `P3`
4. เลือกไฟล์คำศัพท์เฉพาะชุด หรือปล่อยค่าเริ่มต้นเพื่อใช้ทั้งโฟลเดอร์
5. เลือกว่าจะ “ล้างคลังคำก่อน Reload” หรือ append เข้าไปโดยไม่ล้างของเดิม
6. กด “Reload คำจาก DOCX/PDF” ระบบจะอ่านเฉพาะคำจาก cell ตาราง
7. เลือก checkbox ระดับชั้น ป.1-ป.6 ที่ต้องการใช้
8. กำหนดจำนวนหน้าและจำนวนคำต่อหน้า
9. เลือกฟอนท์, orientation, ขนาดฟอนท์ และองศา
10. กำหนด Title และค่าการแสดงผล
11. กด “บันทึกการตั้งค่า” หากต้องการใช้ค่าเดิมครั้งถัดไป
12. กด “สร้าง PDF”

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

คำสั่งนี้เหมาะสำหรับตรวจสอบการสกัดคำโดยตรง และจะรายงานจำนวนคำ unique หลัง import

หลัง reload สำเร็จ ระบบสร้างรายงานตรวจรับที่:

```text
app/doc/evidence/word_import_report.json
```

## ข้อจำกัดปัจจุบัน

- PDF ที่เป็นภาพสแกนยังไม่รองรับ OCR
- ไฟล์ `.doc` ไม่ถูกอ่านโดยตรง ต้องแปลงเป็น `.docx` ก่อน
- PDF ต้องมี text layer และตาราง vector ตาม contract; หาก text layer ของ PDF ผิด ต้องแก้ source หรือทำ visual review ก่อนใช้จริง
- หากจำนวนคำมากเกินพื้นที่แม้ลดถึง minimum แล้ว ระบบจะแจ้งเตือนแทนการสร้างไฟล์ที่คำซ้อนกัน
- ฟอนท์ที่เลือกต้องรองรับ glyph ของภาษาไทย
