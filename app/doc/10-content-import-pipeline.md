# Content Import Pipeline

## 1. Supported source formats

โปรแกรมรองรับ source แบบตาราง 2 รูปแบบ:

| รูปแบบ | สถานะ | เงื่อนไข source |
|---|---|---|
| `.docx` | Production path | ไฟล์ Word ต้องมีคำศัพท์อยู่ในตารางแบบคู่คอลัมน์ `ลำดับ/คำ` หรือ `คำที่/คำ` และชื่อไฟล์ต้องมีระดับชั้น ป.1-ป.6 |
| `.pdf` | Legacy supported path | PDF ต้องมี text layer, vector table lines, cell geometry อ่านได้ และชื่อไฟล์ต้องมีระดับชั้น ป.1-ป.6 |

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

- ไม่พบไฟล์ `.docx` หรือ `.pdf` ที่รองรับในโฟลเดอร์ source
- ชื่อไฟล์ไม่มีระดับชั้น ป.1-ป.6
- ไม่พบคำศัพท์ในตาราง
- cell คำว่างหรือมี control character
- คำยาวผิดปกติเกิน 60 ตัวอักษร
- ระดับชั้นนอกช่วง ป.1-ป.6
- PDF ไม่มี table geometry หรือไม่มี text layer ที่อ่านได้ตาม contract

## 4. Verification evidence

ก่อน import production ให้รัน audit ก่อนเสมอ:

```powershell
F:\programming\python\MTChooseWords\.venv\Scripts\python.exe scripts\audit_word_sources.py
```

Audit report จะถูกสร้างที่:

```text
app/doc/evidence/word_source_audit_report.json
```

สถานะรายไฟล์:

- PASS: ผ่าน contract และไม่พบคำที่ต้อง review
- REVIEW: อ่านได้ แต่มีคำที่ Python สงสัย เช่น cell ยาวมาก คำซ้ำ หรือรูปอักขระที่ควรตรวจ
- FAIL: ห้าม import จนกว่าจะแก้ source หรือปรับ parser พร้อม test

ทุกครั้งที่ reload ผ่าน command line ระบบสร้างรายงาน:

```text
app/doc/evidence/word_import_report.json
```

รายงานต้องมี:

- จำนวน cell คำที่อ่านได้ทั้งหมด
- จำนวนคำ unique หลัง normalize
- จำนวน cell ที่เป็นคำซ้ำ
- จำนวนแยกตามระดับชั้น
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

- `.docx`: ใช้เป็น production path หลัก เพราะอ่านจาก XML table โดยตรง
- `.pdf`: รองรับเพื่อ compatibility แต่ถ้า PDF มี character map ผิดหรือ source ไม่ตรง contract ต้องแก้ source หรือทำ visual review ก่อนนำไปใช้จริง
- AI หรือ OCR ไม่สามารถ overwrite คำศัพท์ production โดยไม่มี human review
- คำที่ยาวจน Word แสดงหลายบรรทัดใน cell เดียวสามารถอ่านได้ แต่ audit จะ mark เป็น `long_cell_review` เพื่อให้ AI/คนตรวจซ้ำ

## 6. Database key and import modes

ฐานข้อมูลใช้ `grade + normalized word` เป็น primary key

Reload มี 2 โหมด:

- clear-all: ล้างคำทั้งหมดก่อน import ชุดใหม่
- append: เพิ่มคำจาก source ที่เลือกเข้าไป โดยข้ามคำที่มี `grade + normalized word` ซ้ำอยู่แล้ว

ผู้ใช้เลือก source ได้หลายไฟล์จาก UI หากไม่เลือกไฟล์เฉพาะ ระบบใช้ทุกไฟล์ที่รองรับใน `words_dir`

Definition of Done สำหรับ content import คือ extractor ผ่าน automated tests, reload สำเร็จ, import report ตรงกับ source ที่ตั้งใจใช้ และไม่มี fail-closed warning เหลืออยู่

Reviewed suspicion registry:

```text
app/assets/words/reviewed_suspicions.json
```

AI review evidence:

```text
app/doc/evidence/ai_word_review_2026-08-26.md
```

## 7. Current PDF source status

PDF source folder `app/assets/words/pdf` has been probed and documented in:

```text
app/doc/evidence/pdf_source_probe.md
```

The adapter supports PDF sources that pass the contract, but this specific PDF batch is not yet certified for 100% production import because some files expose corrupted text-layer output and require visual review or source correction.
