# O/L English Marking Assistant (local, Ollama only)

A marking studio for Sri Lankan G.C.E. O/L English answer scripts. A teacher uploads
a student's scanned script and the marking scheme for that paper. The system reads
both with a vision model running on the same laptop, marks all sixteen tests against
the scheme, and returns a mark out of 100 with feedback, tips and the skill behind
each lost mark. Nothing is sent to a cloud service.

Built as a final year project. It is a teaching and research prototype, not an
accredited marking system, and every mark stays editable by the teacher.

## What it does

- Reads handwritten and printed scripts page by page, with a local vision model.
- Indexes the marking scheme first, so no test can quietly drop out of the report.
- Marks each test point by point against the scheme, not against the model's opinion.
- Normalises every paper to 100 marks, whatever the printed allocations add up to.
- Keeps a knowledge base per teacher: syllabus, past papers, schemes, guidance, plus
  every marked paper as a worked example for later runs.
- Shows an accuracy figure and says which tests were marked against a real answer key
  and which were estimated.

## Requirements

| What | Version | Why |
| --- | --- | --- |
| Python | 3.11 or newer | backend |
| Node.js | 18 or newer | frontend |
| Ollama | latest | runs the local models |
| RAM | 16 GB comfortable, 8 GB possible | 11B vision model |
| Disk | about 12 GB | model weights |

Full setup, including smaller models for an 8 GB machine, is in
[docs/ollama_setup.md](docs/ollama_setup.md).

## Quick start

```bash
# 1. models (once)
ollama pull llama3.2-vision:11b
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 2. backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then put a real JWT_SECRET in it
uvicorn app.main:app --reload --port 8000

# 3. frontend (a second terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, register an account, and the four starter knowledge
sources are added for you. Upload a script and its scheme on **New paper**.

Check the models before the first run:

```bash
curl http://127.0.0.1:8000/api/health/ai
```

It reports whether Ollama is reachable and whether both models are installed.

## Folder structure

```
ol-marking-rag/
├── README.md, docker-compose.yml, .gitignore
├── docs/                     architecture, api, code guide, viva notes, Ollama setup
├── backend/
│   ├── requirements.txt, .env.example, Dockerfile, pytest.ini
│   ├── app/
│   │   ├── main.py           FastAPI app: middleware, lifespan, one router
│   │   ├── db.py             engine, session, table creation
│   │   ├── models.py         SQLAlchemy tables
│   │   ├── api/              deps.py, v1/router.py, v1/routes/{health,auth,papers,marking,rubrics}
│   │   ├── core/             config.py, logging.py, security.py, limits.py
│   │   ├── schemas/          auth.py, paper.py, marking.py, rubric.py
│   │   ├── services/         marking_service, ingestion_service, rubric_service, starter_knowledge
│   │   ├── rag/              llm, embeddings, vectorstore, retriever, loaders, splitter, chains, prompts/
│   │   └── utils/            files.py
│   ├── data/raw/             mark_schemes, rubrics, past_papers, examiner_reports
│   ├── scripts/ingest.py     bulk load data/raw into the knowledge base
│   ├── evaluation/           four evaluation suites and their results
│   └── tests/                chunking, metrics, security, validation
└── frontend/
    ├── package.json, vite.config.js, index.html
    └── src/                  api, components/{layout,common,marking}, pages, hooks, routes, styles, utils
```

## How a marking run works

1. The script and the scheme are stored privately and a background task starts.
2. Each PDF page is rendered in colour at 200 DPI, and script pages are split by ink colour into a printed layer and a handwritten layer.
3. The vision model transcribes the script and the scheme, keeping `=== Qn ===`
   markers so question boundaries survive OCR.
4. The scheme is read once for its question list and mark allocations.
5. The knowledge base is searched for rubric lines that match this paper.
6. The text model marks every listed question, one entry each, as JSON.
7. Rows are normalised to 100 marks, stored, and the paper is indexed as a worked
   example.

The whole run is a LangGraph state machine, so a failure at any step marks the paper
as failed with a message a teacher can act on, instead of leaving it half marked.

## Tests and evaluation

```bash
cd backend
pytest                       # unit tests, no model needed
python -m evaluation.run_all # writes evaluation/results/*.json and *.md
```

The evaluation suite measures structure detection, OCR quality (CER, WER, item
accuracy), retrieval quality and marking agreement (MAE, RMSE, weighted kappa,
Spearman) against hand-marked ground truth.

<!-- ## Documentation

| File | What it covers |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | layers, request flow, data model, design decisions |
| [docs/api.md](docs/api.md) | every endpoint, request and response |
| [docs/code_guide.md](docs/code_guide.md) | what each file does, function by function |
| [docs/viva_qa.md](docs/viva_qa.md) | likely questions and short answers |
| [docs/ollama_setup.md](docs/ollama_setup.md) | installing Ollama and the models | -->

## Limits

- One script and one scheme per run.
- The scheme must be supplied. The system does not invent mark allocations.
- Handwriting that cannot be read is reported as `[illegible]`, never guessed.
- Long papers are cut to the prompt budget, and the paper says when that happened.
- No candidate identification, no plagiarism detection, no grade boundaries.
