# Raw source documents

Drop the real corpus here before bulk loading it, one folder per kind:

```
data/raw/
├── mark_schemes/       official marking schemes, one PDF per paper
├── rubrics/            syllabus and assessment criteria
├── past_papers/        question papers without answers
└── examiner_reports/   examiner reports and guidance notes
```

Then load them into one teacher's knowledge base:

```bash
cd backend
python -m scripts.ingest --email teacher@school.lk
```

The file name becomes the title, so name the files properly, for example
`2019-marking-scheme.pdf` rather than `scan0043.pdf`. Each document is read by the
local OCR model (GLM-OCR), which takes about twenty seconds a page. Nothing here is
committed with real candidate work in it: this folder ships empty on purpose.
