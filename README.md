---
title: INFINITE LOOPS - SIH26038 Retinal Screening
emoji: 👁️
colorFrom: blue
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">

# 👁️ INFINITE LOOPS — SIH26038
### Explainable AI for Diabetic Retinopathy Screening in Rural India

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-orange.svg?style=for-the-badge&logo=target)](https://www.sih.gov.in/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PyTorch & Keras 3](https://img.shields.io/badge/PyTorch%20%7C%20Keras%203-Deep%20Learning-EE4C2C?style=for-the-badge&logo=pytorch)](https://keras.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## ⚕️ Clinical Safety Notice

> **INVESTIGATIONAL USE / CLINICAL DECISION SUPPORT NOTICE**
> This software is an **AI-assisted screening triage prototype** designed to assist healthcare workers and optometrists in identifying referable cases. **It does not provide a definitive medical diagnosis.** All automated assessments must be reviewed and confirmed by a certified ophthalmologist before clinical decisions are made.

---

## 🌍 Problem Context

India has over **101 million diagnosed diabetics** and an additional **136 million pre-diabetics**. Up to 30% will develop **Diabetic Retinopathy (DR)** — a leading cause of preventable blindness. Meanwhile, **>85% of ophthalmologists** practice in urban centers, leaving rural populations without screening access.

This system enables **ASHA workers and PHC staff** to perform retinal screening with automated AI triage and explainable results.

---

## ✨ Key Features

- **Bilateral Retinal Screening:** Simultaneous evaluation of Right Eye (OD) and Left Eye (OS).
- **Real-Time Quality Gate:** Rejects ungradable images (blurry, off-center, underexposed) before patient departure.
- **ICDR Grading (0–4):** No DR → Mild NPDR → Moderate NPDR → Severe NPDR → PDR.
- **Referable DR Alert:** Flags severity ≥ 2 for immediate specialist review.
- **Explainable AI:** Grad-CAM heatmaps + biomarker detection (microaneurysms, hemorrhages, exudates).
- **Guided Recapture Loop:** Dynamic instructions for field operators when image quality fails.

---

## 🛠️ Technology Stack

| Layer | Tech |
|---|---|
| **Frontend** | React 19, TypeScript, Vite 6, Lucide icons |
| **Backend** | FastAPI, Uvicorn, SSE streaming |
| **ML** | PyTorch, Keras 3, EfficientNet-B0, CORAL ordinal regression |
| **Vision** | OpenCV, Pillow |
| **Model Hub** | [Hugging Face Hub](https://huggingface.co/Aldahmashi/DR-EfficientNetB0) |

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** v20+
- **Python** v3.10 / 3.11 / 3.12
- **npm** v10+

### 1. Clone & Install
```bash
git clone https://github.com/simbisaichinhema/AI-for-Diabetic-Retinopathy-Screening-in-Rural-India.git
cd AI-for-Diabetic-Retinopathy-Screening-in-Rural-India
npm install
```

### 2. Set Up Python Environment
```bash
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

### 3. Start Everything
```bash
npm start
```

This runs the FastAPI backend (`:8000`) and Vite dev server (`:5173`) together. The app waits for the ML model to load before the frontend is ready.

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/api/health

### Docker (Optional)
```bash
docker-compose up --build
```
Runs on http://localhost:7860.

---

## 📡 API Reference

### `POST /api/screen-stream` — Streaming Screening
```bash
curl -X POST "http://localhost:8000/api/screen-stream" \
  -H "accept: text/event-stream" \
  -F "file=@public/assets/head_exact_right.jpg"
```
Returns SSE stream with live progress through quality check, inference, Grad-CAM, and lesion detection.

### `POST /api/screen` — Standard Screening
```bash
curl -X POST "http://localhost:8000/api/screen" \
  -F "file=@public/assets/head_reference_right.jpg"
```

### `GET /api/health` — Health Check
```json
{"status": "healthy", "version": "2.0.0"}
```

### `GET /api/models/status` — Model Status
```json
{"warming": false, "models": {"classifier": true}}
```

---

## 🧪 Testing

```bash
# Backend tests
pytest tests/ -v

# Frontend build check
npm run build
```

---

## 📊 Dataset Preparation

Download datasets via Kaggle API (requires `~/.kaggle/kaggle.json`):
```bash
python scripts/download_datasets.py --dataset aptos
```

Run training:
```bash
python training/train_aptos_coral.py
```

---

## 👥 Team

- **Smart India Hackathon 2026**
- **Problem Statement:** SIH26038
- **Team:** INFINITE LOOPS
