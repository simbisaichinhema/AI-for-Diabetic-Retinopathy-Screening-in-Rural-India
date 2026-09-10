

<div align="center">

# INFINITE LOOPS — SIH26038
### Explainable AI for Diabetic Retinopathy Screening in Rural India

**Smart India Hackathon 2026 · Problem Statement SIH26038 · Team INFINITE LOOPS**

</div>

## 🌍 Problem ContextS

India has over 77 million diabetic adults - the second highest globally. Diabetic Retinopathy (DR) affects ~18% of this population and is a leading cause of preventable blindness. Early screening can prevent90% of vision loss, but India has only ~1 ophthalmologist per 100,000 rural population, making mass manual screening infeasible. Existing AI solutions function as black boxes, lack clinical validation rigor, and fail with variable image quality from portable fundus cameras in field conditions. A robust, explainable, and validated screening system is essential for deployment in primary healthcare centres across rural India.


This system lets **ASHA workers and PHC staff** capture fundus photographs and receive
automated AI triage with explainable evidence, so referable cases reach a specialist in time.

---

##  Key Features

- **Bilateral screening** — simultaneous Right Eye (OD) and Left Eye (OS) evaluation.
- **Real-time quality gate** — rejects ungradable images (blur, poor illumination, small
  field of view, non-fundus input) before the patient leaves, with guided recapture instructions.
- **ICDR grading (0–4)** — No DR → Mild → Moderate → Severe → Proliferative DR.
- **Referable-DR alert** — severity ≥ 2 flagged for immediate specialist review.
- **Explainable AI** — Grad-CAM attention heatmaps, CLAHE-enhanced scan view, and lesion
  evidence (microaneurysms, haemorrhages, exudates, vessel analysis).
- **Clinical report** — structured screening report per case with recommendation.
- **Live progress streaming** — stage-by-stage SSE updates from image receipt to report.

---

##  Architecture

```
 fundus photo
     │
     ▼
┌─────────────┐   ┌──────────────┐   ┌───────────────────┐
│ React + Vite │──▶│ FastAPI (SSE)│──▶│ EfficientNet-B0   │
│ workstation  │◀──│ quality gate │◀──│ + CORAL ordinal   │
└─────────────┘   │ lesions /    │   │ grading (5-class) │
                  │ Grad-CAM /   │   └───────────────────┘
                  │ report       │
                  └──────────────┘
```

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 6 |
| Backend | FastAPI, Uvicorn, Server-Sent Events |
| Deep learning | PyTorch, Keras 3, EfficientNet-B0 + CORAL ordinal regression |
| Vision | OpenCV, Pillow |
| Deploy |Render + vercel |

---

##  How to Run It

### Prerequisites

- **Node.js** 20+ and **npm** 10+
- **Python** 3.10, 3.11 or 3.12

### Option A — Full stack locally (recommended for review)

```bash
git clone https://github.com/simbisaichinhema/AI-for-Diabetic-Retinopathy-Screening-in-Rural-India.git
cd AI-for-Diabetic-Retinopathy-Screening-in-Rural-India

# 1. Frontend dependencies
npm install

# 2. Python environment
python3 -m venv ../.venv
source ../.venv/bin/activate        # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt

# 3. Start backend + frontend together
npm start
```

Then open:

- **Workstation:** http://localhost:5173
- **API health:** http://localhost:8000/api/health
- **API docs:** http://localhost:8000/docs

On first start the backend downloads the trained classifier weights once and caches them;
screening a first image can take 60–120 s on CPU, then it is fast. Sample fundus images for
a walkthrough live in `public/assets/`.

### Option B — Docker (single container, port 7860)

```bash
docker-compose up --build
```

Open http://localhost:7860. The same workstation is served by the backend container.

### Option C — Split cloud deploy (Vercel + Render)

- Frontend → Vercel: framework **Vite**, build `npm run build`, output `dist`,
  env `VITE_API_BASE_URL=https://<render-service>.onrender.com`.
- Backend → Render: `dr-screening-backend` service, free plan,
  build `pip install -r requirements.txt`,
  start `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`.

---

##  How to Take a Screening (operator walkthrough)

1. Open the workstation and start a new session.
2. Capture or upload the **Right Eye (OD)** fundus photo, then the **Left Eye (OS)**.
3. The **quality gate** scores focus, illumination, field of view and fundus validity.
   If it fails, follow the on-screen recapture guidance and retake — do not proceed.
4. Click **Proceed to AI Retinal Analysis**. Watch live stages: quality → preprocessing →
   inference → referable check → lesion analysis → Grad-CAM → report.
5. Review the grade (0–4), referable flag, lesion evidence and heatmap.
6. Export or escalate the **clinical report**; refer grades ≥ 2 to an ophthalmologist.

---

##  Datasets — Where Every Image Comes From

No dataset is bundled with this repo (they are too large and carry their own licences).
Each one is fetched from its original public source and lands under `data/`.
Layout, splits and preprocessing defaults live in `configs/dataset_config.yaml`.

| Dataset | Source (origin) | How to obtain | Contents | Role in this project |
|---|---|---|---|---|
| **APTOS 2019 Blindness Detection** | Kaggle competition `aptos2019-blindness-detection` (Aravind Eye Hospital images) | Automatic: `python scripts/download_datasets.py --dataset aptos` (needs `~/.kaggle/kaggle.json`, `chmod 600`; token from kaggle.com/settings) | ~3,662 fundus photos + `train.csv` with 5-class ICDR grades | **Primary training data** for the DR grader (`train_aptos_coral.py`, `train_aptos.py`) |
| **IDRiD** (Indian Diabetic Retinopathy Image Dataset) | https://idrid.grand-challenge.org/ | Manual download (challenge registration), extract to `data/idrid/` | 516 images + DR grades + pixel-level lesion masks (microaneurysms, haemorrhages, exudates) | Trains the lesion-segmentation branch (`train_idrid_lesions.py`); ground truth behind the lesion-evidence panel |
| **DRIVE** (Digital Retinal Images for Vessel Extraction) | https://drive.grand-challenge.org/ (Utrecht) | Manual download, extract to `data/drive/` | 40 images + vessel-segmentation masks | Trains the vessel-analysis branch (`train_drive_vessels.py`) |
| **Messidor-2** | http://www.adris.net/messidor2 (registration required) | Manual download after registration, extract to `data/messidor2/` | 1,748 images + DR grades + macular-edema risk | **Independent validation** — cross-dataset check that the grader generalises (`cross_dataset_validation.py`) |
| **Synthetic sample** | Generated locally, no download | `python scripts/download_datasets.py --dataset sample` (the default) | 100 generated fundus-like images (20 per grade) + `train.csv` | Smoke-tests the full training path in seconds without credentials (`scripts/run_training.py`) |

One command for everything the script can fetch:

```bash
python scripts/download_datasets.py --dataset all
```

> Licence note for reviewers: APTOS is under its Kaggle competition terms; IDRiD, DRIVE
> and Messidor-2 each carry their own research-use terms from the links above. That is why
> `data/` only ever holds local copies — nothing is redistributed here.

---

## How to Train the Models

Training configs live in `configs/config.yaml`. Outputs go to `models/` (git-ignored).

### 1. DR grader — EfficientNet + CORAL (primary model, APTOS)

Two-stage transfer learning with CORAL ordinal regression, QWK cutoff search and
held-out evaluation:

```bash
# Full training on real APTOS data
python training/train_aptos_coral.py --data-dir data/aptos

# Download from Kaggle first, then train
python training/train_aptos_coral.py --download

# Quick smoke run on sample data (5 epochs, verifies the pipeline)
python scripts/run_training.py
```

Plain cross-entropy variant (no CORAL):

```bash
python training/train_aptos.py
```

### 2. Vessel segmentation — DRIVE

```bash
python training/train_drive_vessels.py
```

### 3. Lesion segmentation — IDRiD

```bash
python training/train_idrid_lesions.py
```

### 4. Evaluate and calibrate

```bash
# Grader metrics on held-out APTOS split (accuracy, QWK, per-class report)
python training/evaluate_aptos.py

# Generic evaluation + cross-dataset validation + probability calibration
python training/evaluate.py
python training/cross_dataset_validation.py
python training/calibration.py
```

### 5. Smoke-test a trained model end to end

```bash
python test_model.py --image public/assets/head_reference_right.jpg
```

This loads the weights, runs preprocessing + inference on one image, prints the grade,
confidence, referable probability and quality-gate verdict, and asserts the output contract.

---

##  API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/screen-stream` | SSE stream: stage events then final result |
| `POST` | `/api/screen` | Single-shot screening (multipart `file`, max 10 MB) |
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/models/status` | Classifier loaded / warming / error |

```bash
# Streaming (live progress)
curl -X POST "http://localhost:8000/api/screen-stream" \
  -H "accept: text/event-stream" \
  -F "file=@public/assets/head_exact_right.jpg"

# Single-shot
curl -X POST "http://localhost:8000/api/screen" \
  -F "file=@public/assets/head_reference_right.jpg"
```

Successful responses carry `status: "completed"` with `quality`, `dr_prediction`
(grade, label, confidence, 5-class probabilities), `referable_dr`, `lesions`,
`gradcam_image` + `enhanced_image` (base64) and `report`. Ungradable images return
`status: "recapture_required"` with the quality reasons.

---

##  Testing

```bash
# Backend suite (quality gate, preprocessing, classifier, pipeline)
pytest tests/ -v

# Frontend production-build check
npm run build
```

---

##  Project Structure

```
src/               React workstation (components, services, types)
backend/           FastAPI app (screen, screen-stream, health, model status)
inference/         quality gate, classifier, pipeline, lesions, report
preprocessing/     quality metrics, transforms, CLAHE, retinal crop
explainability/    Grad-CAM, confidence, lesion evidence
training/          APTOS/CORAL, DRIVE vessels, IDRiD lesions, evaluation
configs/           training + dataset configuration
scripts/           dataset download, sample training, API smoke test
tests/             backend test suite
public/assets/     sample fundus images for walkthroughs
```

---

##  Note on Model Weights (fallback)

The weights used at review time are downloaded once from a public model repository and
cached locally — this is a convenience fallback so reviewers never need large files.
The authoritative path is training from source with the scripts above; any compatible
`.keras` classifier can be pointed to via `DR_MODEL_ID` / `DR_MODEL_FILE`.

---

##  Team

- **Event:** Smart India Hackathon 2026
- **Problem Statement:** SIH26038 — AI for Diabetic Retinopathy Screening in Rural India
- **Team:** INFINITE LOOPS
