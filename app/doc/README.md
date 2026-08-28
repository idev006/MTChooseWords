# MT Choose Words — Project Documentation

เอกสารชุดนี้เป็นแหล่งข้อมูลหลักของโครงการ (Single Source of Truth) สำหรับการพัฒนาแบบ **Document-Driven Project** และการบริหารงานแบบ **Kanban Agile**

## เอกสารหลัก

- [วิสัยทัศน์และข้อกำหนดผลิตภัณฑ์](01-product-requirements.md)
- [สถาปัตยกรรมระบบ](02-architecture.md)
- [Kanban Board และ Backlog](03-kanban-board.md)
- [บันทึกการตัดสินใจทางสถาปัตยกรรม](04-architecture-decisions.md)
- [แผนการทดสอบและเกณฑ์ยอมรับ](05-test-plan.md)
- [Test Cases และ Test Report](07-test-cases.md)
- [กรณีสกัดภาษาไทยจาก PDF](08-thai-pdf-extraction.md)
- [Content Import Pipeline](10-content-import-pipeline.md)
- [Feature Recommendations](11-feature-recommendations.md)
- [คู่มือการติดตั้งและใช้งาน](06-user-guide.md)
- [PDF Source Probe Evidence](evidence/pdf_source_probe.md)
- [PDF Source Diagnosis JSON](evidence/pdf_source_diagnosis.json)
- [PDF OCR Cell Diagnosis JSON](evidence/pdf_ocr_cell_diagnosis.json)
- [PDF OCR Folder Read Report](evidence/pdf_ocr_folder_read_report.json)
- [PDF OCR Review Queue CSV](evidence/pdf_ocr_review_queue.csv)
- [AI Word Review Evidence](evidence/ai_word_review_2026-08-26.md)
- [บันทึกการเปลี่ยนแปลง](CHANGELOG.md)

## หลักการทำงาน

1. งานใหม่ต้องเริ่มจากการเขียนหรือปรับเอกสารที่เกี่ยวข้อง
2. ทุกงานต้องมี Acceptance Criteria ที่ตรวจสอบได้
3. จำกัดงานที่กำลังทำ (WIP Limit) เพื่อให้งานเสร็จเป็นชิ้น ๆ
4. การเปลี่ยนแปลงสำคัญต้องบันทึกใน ADR
5. ก่อนย้ายงานไป Done ต้องผ่านการทดสอบและอัปเดตเอกสาร
6. Source code แต่ละไฟล์ต้องมีไม่เกิน 700 บรรทัด หากใกล้เกินขนาดต้องแยกเป็นโมดูลย่อย

## สถานะเอกสาร

เอกสารนี้ครอบคลุม baseline ของ MVP, DOCX/TXT production import pipeline, import audit/preview gate, source-folder journal และ PDF OCR diagnostic review queue ณ วันที่ 2026-08-28
