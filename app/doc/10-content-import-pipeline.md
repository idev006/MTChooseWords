# Content Import Pipeline

## 1. Supported source formats

โปรแกรมรองรับ source สำหรับ production 2 รูปแบบ:

| รูปแบบ | สถานะ | เงื่อนไข source |
|---|---|---|
| `.docx` | Production path | ไฟล์ Word ต้องมีคำศัพท์อยู่ในตารางแบบคู่คอลัมน์ `ลำดับ/คำ` หรือ `คำที่/คำ` และชื่อไฟล์ต้องมีระดับชั้น ป.1-ป.6 |
| `.txt` | Production path | ไฟล์ text UTF-8 ต้องมีหนึ่งคำต่อหนึ่งบรรทัด และชื่อไฟล์ต้องมีระดับชั้น ป.1-ป.6 เช่น `คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt` |

ไม่มีตัวอ่านคำจาก PDF/OCR ใน local code แล้ว เพราะยังไม่มี approval workflow ที่รับประกันความถูกต้องได้พอสำหรับงานการศึกษา

ไฟล์ `.doc` ยังไม่ถูกอ่านโดยตรง หากต้องการใช้ต้องแปลงเป็น `.docx` ก่อน

## 2. Table-only rule

Importer อ่านเฉพาะ cell ในตารางที่จับคู่เลขลำดับกับ cell คำได้เท่านั้น:

```text
ที่/คำ
คำที่/คำ
เลขลำดับ/คำศัพท์
```

ระบบไม่อ่านข้อความหัวเรื่อง ย่อหน้า footer หรือคำอธิบายนอกตารางเข้า database

## 3. Fail-closed gates

การ import ต้องหยุดทันทีเมื่อพบเงื่อนไขต่อไปนี้:

- ไม่พบไฟล์ `.docx` หรือ `.txt` ที่รองรับในโฟลเดอร์ source
- ชื่อไฟล์ไม่มีระดับชั้น ป.1-ป.6
- ไม่พบคำศัพท์ในตาราง
- cell คำว่างหรือมี control character
- คำยาวผิดปกติเกิน 120 ตัวอักษร
- ระดับชั้นนอกช่วง ป.1-ป.6
- เลือกเฉพาะ PDF หรือโฟลเดอร์ที่ไม่มี `.docx`/`.txt` ที่รองรับ

คำที่ยาวเกิน 40 ตัวอักษรยังอ่านได้ แต่ระบบจะจัดเป็น REVIEW เพื่อให้ AI/ทีมวิชาการตรวจรับก่อนใช้จริง เพราะอาจเป็นคำหรือวลีที่ Word แสดงหลายบรรทัดใน cell เดียว

## 4. Verification evidence

ก่อน import production ให้รัน audit ก่อนเสมอ:

```powershell
.\.venv\Scripts\python.exe scripts\audit_word_sources.py
```

Audit report จะถูกสร้างที่:

```text
app/doc/evidence/word_source_audit_report.json
```

สถานะรายไฟล์:

- PASS: ผ่าน contract และไม่พบคำที่ต้อง review
- REVIEW: อ่านได้ แต่มีคำที่ Python สงสัย เช่น cell ยาวมาก คำซ้ำ หรือรูปอักขระที่ควรตรวจ
- FAIL: ห้าม import จนกว่าจะแก้ source หรือปรับ parser พร้อม test

Audit command ต้องคืน exit code ไม่ผ่านเมื่อมี `FAIL` หรือ `REVIEW` เพื่อกันไม่ให้ CI/release pipeline ผ่านโดยยังมีคำที่ไม่ได้ตรวจรับ

ทั้ง UI และ command line ใช้ audit gate เดียวกันผ่าน `app/core/import_audit.py` ดังนั้น Reload จะถูกบล็อกก่อนเขียน database หากยังมีไฟล์สถานะ `FAIL` หรือ `REVIEW`

โครงอ่าน source ใช้ adapter registry ใน `app/core/source_adapters.py` โดย registry เปิดเฉพาะ DOCX/TXT เพื่อให้ test และการเพิ่ม parser ในอนาคตทำได้โดยไม่กระทบ UI, database หรือ audit gate

ทุกครั้งที่ audit อ่าน source จะสร้าง journal ในโฟลเดอร์ source:

```text
mtchoosewords_import_journal.json
```

Journal ต้องมี source formats ที่ production รองรับ, inputs, source ที่อ่านจริง, summary, can_import, error และรายละเอียดรายไฟล์

ทุกครั้งที่ reload ผ่าน UI หรือ command line ระบบสร้างรายงาน:

```text
app/doc/evidence/word_import_report.json
```

รายงานต้องมี:

- จำนวน cell คำที่อ่านได้ทั้งหมด
- จำนวนคำ unique หลัง normalize
- จำนวน cell ที่เป็นคำซ้ำ
- จำนวนแยกตามระดับชั้นด้วยคีย์ `ป.1` ถึง `ป.6`
- รายชื่อ source file ที่ใช้จริง

## 4.1 AI-assisted review loop

ช่วงพัฒนาให้ใช้ workflow นี้:

1. Python audit อ่าน source และแยกคำที่สงสัย
2. AI/ทีมวิชาการตรวจ `word_source_audit_report.json`
3. ถ้าเป็นคำถูกแต่ยาว/พิเศษ ให้บันทึกใน `app/assets/words/reviewed_suspicions.json` พร้อมหลักฐาน review
4. ถ้าเป็นคำผิดจาก parser หรือ text layer ให้แก้ parser/source และรัน audit ใหม่
5. Import production ได้เฉพาะเมื่อไม่มี FAIL และ REVIEW ได้รับการตรวจรับแล้ว

## 5. Accuracy policy

สำหรับงานการศึกษา ห้าม import แบบเดาสุ่มหรือปล่อยผ่านข้อมูลที่ไม่ผ่าน contract

- `.docx`: ใช้เป็น production path เพราะอ่านจาก XML table โดยตรง
- `.txt`: ใช้เป็น production path สำหรับชุดคำที่ visual verified แล้ว เพราะหนึ่งบรรทัดเท่ากับหนึ่งคำและตรวจนับง่าย
- AI หรือ OCR ไม่สามารถ overwrite คำศัพท์ production โดยไม่มี human review
- คำที่ยาวจน Word แสดงหลายบรรทัดใน cell เดียวสามารถอ่านได้ แต่ audit จะ mark เป็น `long_cell_review` เพื่อให้ AI/คนตรวจซ้ำ
- หากจะนำ PDF/OCR reader กลับมาในอนาคต ต้องมี expected list ที่คนตรวจรับแล้ว, review queue ที่ใช้งานจริงได้ และ approval log ที่ตรวจย้อนหลังได้ก่อน

## 6. Database key and import modes

ฐานข้อมูลใช้ `grade key + normalized word` เป็น primary key โดย `grade key` ต้องเป็นข้อความ `ป.1`, `ป.2`, `ป.3`, `ป.4`, `ป.5` หรือ `ป.6` เท่านั้น

ก่อนสร้าง key และบันทึกคำ ระบบต้อง trim หัวท้ายและ collapse ช่องว่างภายในคำให้เหลือรูปมาตรฐานเดียวกัน เช่น ` กา ` และ `กา` ในระดับ `ป.1` ต้องถือเป็นคำเดียวกัน

Command line reload มี 2 โหมด:

- clear-all: ล้างคำทั้งหมดก่อน import ชุดใหม่
- append: เพิ่มคำจาก source ที่เลือกเข้าไป โดยข้ามคำที่มี `grade key + normalized word` ซ้ำอยู่แล้ว

UI แยกคำสั่งเป็น 2 ปุ่มเพื่อป้องกันความสับสน:

- “ล้างข้อมูลคำในฐานข้อมูล”: ล้างคำทั้งหมดอย่างเดียว หลังผู้ใช้ยืนยัน
- “นำเข้ารายการคำ”: audit source แล้วเพิ่ม/อัปเดตคำ โดยไม่ล้างข้อมูลเดิม

ผู้ใช้เลือก source ได้หลายไฟล์จาก UI หากไม่เลือกไฟล์เฉพาะ ระบบใช้ทุกไฟล์ที่รองรับใน `words_dir`

เมื่อ import รวมหลาย source เช่น `app/assets/words/lot1` และ `app/assets/words/text` รายงาน duplicate ต้องนับข้าม source ด้วย หากคำเดียวกันอยู่ในระดับชั้นเดียวกันทั้ง DOCX และ TXT ต้องถือว่าเป็น duplicate ตามคีย์ `ป.x + คำ`

ก่อนนำเข้ารายการคำใน UI ระบบจะแสดง preview ให้ผู้ใช้ยืนยัน โดยสรุปจำนวน source, จำนวน cell คำที่อ่านได้ และจำนวนคำไม่ซ้ำ หากผู้ใช้ไม่ยืนยันจะไม่มีการเขียน database

Definition of Done สำหรับ content import คือ extractor ผ่าน automated tests, audit gate PASS, ผู้ใช้ยืนยัน preview, reload สำเร็จ, import report ตรงกับ source ที่ตั้งใจใช้ และไม่มี fail-closed warning เหลืออยู่

Reviewed suspicion registry:

```text
app/assets/words/reviewed_suspicions.json
```

AI review evidence:

```text
app/doc/evidence/ai_word_review_2026-08-26.md
```

## 7. Removed PDF/OCR source reader

โค้ดอ่านคำจาก PDF/OCR ถูกถอดออกจาก local scope แล้ว ได้แก่ core reader, diagnostic scripts, OCR evidence และ dependency เฉพาะทาง การนำเข้าคำจึงเหลือเฉพาะ `.docx` และ `.txt` เท่านั้น ส่วน PDF ยังใช้เป็นไฟล์ผลลัพธ์ของใบงาน
