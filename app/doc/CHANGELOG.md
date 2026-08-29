# Changelog

## 2026-08-29 — Portable release preparation

- เพิ่ม `scripts/build_portable.py` และ `Build_Portable_MTChooseWords.bat` สำหรับสร้างโฟลเดอร์ `dist/MTChooseWords_Portable` และไฟล์ `dist/MTChooseWords_Portable.zip`
- เพิ่ม `Run_MTChooseWords_Portable.bat` สำหรับเปิด EXE จาก portable folder พร้อมตรวจ config, database และ fonts
- ปรับ PyInstaller spec เป็น one-dir runtime ไม่ใช่ one-file EXE เพื่อลดความเสี่ยง `QtCore` DLL load error และให้ Qt DLL อยู่ข้าง EXE
- แก้ปัญหา packaged EXE ดึง `icudt78.dll`/`icuuc.dll` ผิดชุดจาก runtime อื่นในเครื่องพัฒนา จนทำให้ `PySide6.QtCore` import ล้มเหลว
- ไม่ bundle `config.toml` และ `app/assets` เข้า EXE เพื่อหลีกเลี่ยงการพ่วง PDF/source เก่าและให้ config/database/assets อยู่ข้างโปรแกรมแบบแก้ไขได้
- ตั้งค่า release config กลับไปใช้ source DOCX/TXT ทั้ง `app/assets/words/lot1` และ `app/assets/words/text` พร้อมเลือก ป.1-ป.6 เป็นค่าเริ่มต้น
- เพิ่มเอกสาร `12-portable-release-checklist.md` และ automated tests สำหรับ portable packaging boundary
- เพิ่ม visual smoke test จาก ZIP ที่แตกไป Temp path ใหม่ โดยยืนยันว่าเห็นหน้าต่าง `MT Choose Words — สร้าง PDF คำศัพท์` จริงและไม่มี dialog error `QtCore`
- ระบุชัดเจนว่าห้าม zip จาก root โครงการหรือรายการ developer files ที่เลือกเอง ต้องแจกเฉพาะ `dist\MTChooseWords_Portable.zip` ที่ออกจาก build pipeline

## 2026-08-29 — Remove PDF/OCR word reader

- ปรับ `Run_MTChooseWords.bat` ให้เป็น batch file สำหรับเปิดโปรแกรมโดยตรง พร้อมตรวจ `.venv` และ `config.toml`
- ถอด core reader, diagnostic scripts, OCR evidence และ tests ที่ใช้สำหรับอ่านคำจาก PDF/OCR ออกจาก local scope
- ถอด dependency เฉพาะทางของ PDF/OCR reader ออกจาก `requirements.txt` และ PyInstaller spec
- เพิ่ม `Cleanup_Unused_PDF_OCR_Libs.bat` สำหรับถอน library PDF/OCR reader เก่าจาก `.venv` ของโครงการแบบมีขั้นตอนยืนยัน
- ปรับ source adapter ให้รองรับเฉพาะ DOCX/TXT สำหรับการนำเข้าคำ
- เก็บ PDF export สำหรับใบงานไว้ผ่าน ReportLab ตามเดิม
- ปรับเอกสาร, test cases และเมนู batch ให้สื่อสารชัดว่า import คำอ่านจาก DOCX/TXT เท่านั้น

## 2026-08-28 — Portable path manager

- เพิ่ม `PathManager` กลางสำหรับ resolve path จาก application root ทั้ง source mode และ PyInstaller mode
- ปรับ UI, config และ scripts ให้ใช้ relative project paths สำหรับ config, source, database, output และ evidence report
- ปรับ journal/import/audit reports และ SQLite `source_file` ให้เก็บ path แบบ relative เมื่ออยู่ใต้ project root
- เพิ่ม automated tests กัน absolute path หลุดใน config/evidence/database และทดสอบ path manager behavior

## 2026-08-28 — Separate clear and import actions

- ปรับ UI tab นำเข้าข้อมูลให้มีปุ่ม “ล้างข้อมูลคำในฐานข้อมูล” และ “นำเข้ารายการคำ” แยกกันชัดเจน
- ปุ่มนำเข้ารายการคำจะ audit source แล้ว add/upsert คำโดยไม่ล้างข้อมูลเดิม
- ปุ่มล้างข้อมูลคำต้องยืนยันก่อน และทำเฉพาะการล้าง database โดยไม่อ่าน source หรือ import คำ
- เพิ่ม automated tests ยืนยันว่า import worker/clear worker ไม่ทำงานปนกัน และ UI smoke test ยืนยันชื่อปุ่มจริงบนหน้าต่าง

## 2026-08-28 — Canonical grade keys and combined duplicate audit

- ปรับฐานข้อมูลให้เก็บระดับชั้นเป็น key รูปแบบ `ป.1` ถึง `ป.6` ตามที่ผู้ใช้กำหนด
- บังคับ trim/collapse ช่องว่างของคำก่อนสร้าง normalized key และก่อนบันทึกลงฐานข้อมูล
- ยืนยัน unique key เป็น `ป.x + normalized word` ดังนั้นคำเดียวกันในระดับเดียวกันจาก DOCX/TXT จะถูกนับเป็น duplicate
- ปรับ import/audit report และ source-folder journal ให้แสดงระดับชั้นเป็น `ป.x`
- ทดสอบ source จริงรวม `app/assets/words/lot1` และ `app/assets/words/text` ผ่าน 12 ไฟล์ ได้ 14,374 cells, 8,705 unique words และ 5,669 duplicate cells
- เพิ่ม automated tests สำหรับ canonical grade key, trim และ duplicate ข้าม DOCX/TXT
- เพิ่ม certification tests สำหรับ source จริง, committed SQLite database, config production-safe และ schema migration จาก grade แบบ integer
- ปรับ `config.toml` ให้ใช้ DOCX/TXT production source และนำฐานข้อมูล SQLite baseline ขึ้น git

## 2026-08-28 — TXT source import and source journals

- เพิ่มตัวอ่าน `.txt` แบบหนึ่งคำต่อหนึ่งบรรทัด โดยอ่านระดับชั้นจากชื่อไฟล์ เช่น `คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt`
- เพิ่ม TXT adapter เข้า production source registry คู่กับ DOCX โดย PDF ยังเป็น diagnostic-only
- เพิ่ม source-folder journal `mtchoosewords_import_journal.json` ทุกครั้งที่ audit อ่าน source
- ปรับ UI file picker และปุ่ม Reload เป็น DOCX/TXT
- ทดสอบ source จริง `app/assets/words/text` ผ่าน 6 ไฟล์ ได้ 8,192 unique words และไม่มี duplicate
- เพิ่ม automated tests สำหรับ TXT extraction, production registry และ journal

## 2026-08-28 — Disable PDF production import

- ปิด PDF จาก production import ชั่วคราวเพื่อป้องกันคำที่ยังไม่ผ่านการตรวจรับเข้าสู่ฐานข้อมูล
- ปรับ default source registry ให้ไม่รับ PDF สำหรับ UI, audit และ reload
- คงเครื่องมือ PDF diagnosis/OCR review queue ไว้สำหรับ QA และสร้างหลักฐาน โดยไม่ import เข้า database
- ปรับ UI file picker และข้อความ Reload ให้ไม่เสนอ PDF เป็น production source
- เพิ่ม automated tests ยืนยันว่า default importer ไม่รับ PDF แต่ diagnostic registry ยังใช้ PDF adapter ได้

## 2026-08-26 — DOCX word-bank and grade selection

- เพิ่ม DOCX table importer สำหรับอ่านเฉพาะคำศัพท์ในตารางจาก `app/assets/words/lot1`
- เพิ่ม multi-format source extractor รองรับ `.docx` และ `.pdf` แบบ table-based
- เพิ่ม source contract validator และ import evidence report
- เพิ่มข้อมูลระดับชั้นในฐานข้อมูลและ query/filter ตาม ป.1-ป.6
- เปลี่ยน schema ให้ `grade + normalized word` เป็น primary key
- เพิ่ม checkbox เลือกระดับชั้นใน UI และบันทึกลง `config.toml`
- เพิ่ม file picker สำหรับเลือก source หลายไฟล์ และโหมด clear-all/append
- ปรับ Reload ให้ใช้ไฟล์ `.docx`/`.pdf` และข้าม `.doc`
- เพิ่ม `scripts/audit_word_sources.py` สำหรับรายงานคำที่ Python สงสัยก่อน import
- เพิ่ม long-cell review policy สำหรับคำยาวที่อาจแสดงหลายบรรทัดใน Word/PDF
- เพิ่ม reviewed suspicion registry และ AI review evidence สำหรับคำที่ตรวจรับแล้ว
- เพิ่ม automated tests สำหรับ DOCX table-only extraction และ grade filtering
- เพิ่ม import audit gate กลางให้ UI และ command line ใช้ร่วมกัน
- ปรับ Reload ให้บล็อกก่อนเขียนฐานข้อมูลเมื่อ source ยังมี REVIEW/FAIL
- เพิ่ม preview ยืนยันก่อน Reload ใน UI พร้อมสรุปจำนวนไฟล์/cell/คำไม่ซ้ำ/โหมดนำเข้า
- ปรับ UI ไม่ให้ auto-reload ตอนเปิดโปรแกรม แต่แสดงจำนวนคำในคลังปัจจุบันแทน
- แยกหน้าจอหลักเป็น 2 tab: นำเข้าข้อมูล และ สร้างใบงาน
- ย้ายงาน audit/reload คำศัพท์ไปทำใน worker thread และแสดง progress/status เพื่อลดปัญหาหน้าจอค้าง
- แยก source reader เป็น adapter registry เพื่อให้ test/plug adapter ใหม่ได้ง่ายขึ้น
- เพิ่ม `scripts/diagnose_pdf_sources.py` สำหรับตรวจ PDF รายหน้าโดยไม่ import เข้า database
- เพิ่ม OCR cell diagnosis สำหรับตรวจ PDF ที่ text layer เพี้ยน โดยยังไม่เปิด import production แบบ OCR จนกว่าจะมี expected output ตรวจรับ
- เพิ่ม coverage calculation ให้ OCR cell diagnosis เพื่อวัดเกณฑ์อ่านได้อย่างน้อย 90% ต่อหน้าที่มี expected count
- เพิ่มคำสั่งอ่าน PDF ทั้งโฟลเดอร์แบบ OCR review queue พร้อม timeout ต่อหน้า, JSON report, CSV สำหรับผู้ใช้ตรวจ และ evidence crop image
- ปรับ OCR diagnostic ให้เก็บคำที่อ่านได้แต่เลขลำดับน่าสงสัยเข้า REVIEW พร้อมหลักฐาน แทนการตัดทิ้ง

## 2026-07-26 — MVP baseline

- เพิ่มเอกสารโครงการแบบ Document-Driven Project
- เพิ่ม Kanban board และ Definition of Done
- บันทึก architecture decisions สำหรับ PySide6, SQLite/SQLAlchemy, ReportLab และ collision strategy
- บันทึกแผนทดสอบและคู่มือผู้ใช้
- เปลี่ยนตัวสกัดคำเป็น table-cell extraction ด้วย pdfplumber
- รองรับการแก้ลำดับ Unicode ของสระ/วรรณยุกต์ไทยจากตำแหน่ง glyph ใน PDF
- เพิ่ม `scripts/reload_words.py` และปุ่ม Reload ใน UI
- ตรวจสอบ PDF ปัจจุบันได้ 1,210 คำ unique จากตาราง 41 หน้า
- เพิ่มกฎบังคับให้ source code แต่ละไฟล์ไม่เกิน 700 บรรทัด
- เพิ่ม pytest configuration, unit tests และ PyInstaller spec
- เพิ่ม package entry point `python -m app`
- ทดสอบ PyInstaller build สำเร็จเป็น `dist/MTChooseWords.exe`
- เพิ่ม test contracts, integration test ของ PDF จริง และ test report
- แก้ปัญหา Thai PDF `/ToUnicode` mapping ทำให้ `ตำลึง` อ่านเป็น `ตาลึง`
- เพิ่ม dictionary-backed Thai normalization และ regression tests
- เพิ่ม `MTChooseWords.bat` สำหรับเปิดโปรแกรม, Reload, Test และ Build ผ่านเมนูเดียว
- ประยุกต์แนวคิด cell-based extraction ด้วย `find_tables()` และอ่าน glyph เฉพาะใน cell
- ระบุการใช้ Thai dictionary จาก `pythainlp` ในสถาปัตยกรรมและเกณฑ์การซ่อมคำ
- ปรับ layout engine ให้ลองจัดวางใหม่หลายรอบและวางคำยาวก่อน ลดปัญหาคำลำดับท้ายจัดวางไม่ได้
