# 🎯 AI Interview Coach

AI Interview Coach is a Streamlit prototype that helps candidates practise common interview questions, review answer content, and receive supportive feedback about visible delivery cues.

## ✨ Features

- 🎓 Field-specific interview questions
- 🧠 NLP answer analysis using TF-IDF and cosine similarity
- 🔑 Keyword feedback and missing ideas
- 🔴 Live webcam and 📤 recorded-video analysis
- 👁️ YOLO person detection and annotated frames
- 😊 Visible facial-expression estimates and 👋 hand gestures
- 📊 Overall practice summary

## 🧩 Models and libraries

| Item | Full name | Purpose | Source |
|---|---|---|---|
| NLP | Natural Language Processing | Analyses the written answer | Project addition |
| TF-IDF | Term Frequency–Inverse Document Frequency | Converts important words into numbers | Project addition |
| Cosine Similarity | Vector similarity measurement | Compares candidate and sample answers | Project addition |
| YOLO | You Only Look Once | Detects a person and annotates video | Tutor notebooks |
| OpenCV | Open Source Computer Vision Library | Reads and processes frames | Tutor notebooks |
| MediaPipe | Face and hand landmark framework | Supports expression and gesture rules | Project addition |
| Streamlit | Python web-app framework | Builds the interface | Project addition |
| streamlit-webrtc | Browser video component | Connects webcam video to Streamlit | Project addition |

## 🛡️ Limitation

The video feature estimates visible expressions, gestures, and camera visibility. It cannot know true feelings, diagnose nervousness, measure personality, or make hiring decisions.

## ▶️ Run the app

Open Git Bash inside the project folder and run each command separately:

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

YOLO downloads `yolo11n.pt` automatically the first time, so internet is needed for the first run.

## 📁 Files

- `app.py` — Streamlit interface
- `interview_utils.py` — answer scoring and summary
- `video_utils.py` — YOLO, OpenCV, face, and hand analysis
- `questions.csv` — interview question bank
- `requirements.txt` — required libraries
- `DEMO_SCRIPT.txt` — presentation guide


