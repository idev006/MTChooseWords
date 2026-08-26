# AI Word Review — 2026-08-26

Source:

```text
app/doc/evidence/word_source_audit_report.json
```

Review result:

- Duplicate items in the same grade are accepted as source duplicates because the database primary key `grade + normalized word` keeps only one usable copy.
- Long cells are accepted as one learning item when they are clearly a phrase, sentence, proverb, or proper name from the source table.
- No AI-generated replacement word was introduced.
- No OCR correction was applied.

Approved review registry:

```text
app/assets/words/reviewed_suspicions.json
```

Items approved:

| Grade | Text | Reason | Decision |
|---|---|---|---|
| ป.1 | ชิ้น | duplicate_in_same_grade | Keep one copy |
| ป.2 | สด | duplicate_in_same_grade | Keep one copy |
| ป.3 | รู้อะไรไม่สู้รู้วิชา รู้รักษาตัวรอดเป็นยอดดี | long_cell_review | Keep as one cell item |
| ป.3 | หลง | duplicate_in_same_grade | Keep one copy |
| ป.3 | โอ้เอ้วิหารราย | duplicate_in_same_grade | Keep one copy |
| ป.5 | โฉมตรู | duplicate_in_same_grade | Keep one copy |
| ป.5 | สมเด็จพระเทพรัตนราชสุดาฯ สยามบรมราชกุมารี | long_cell_review | Keep as one cell item |
| ป.5 | ประวัติศาสตร์ | duplicate_in_same_grade | Keep one copy |
| ป.6 | คนที่ไม่มีจุดมุ่งหมายใดในชีวิต เปรียบเสมือนเรือไม่มีหางเสือ | long_cell_review | Keep as one cell item |
| ป.6 | นมัสการ | duplicate_in_same_grade | Keep one copy |
| ป.6 | นักขัตฤกษ์ | duplicate_in_same_grade | Keep one copy |
| ป.6 | เศียร | duplicate_in_same_grade | Keep one copy |

Remaining requirement:

Any new unresolved suspicion in future audits must be reviewed before production import.
