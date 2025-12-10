---
description: Start AfundiOS backend and frontend together
---
# AfundiOS – start backend & frontend

## 1️⃣ Install dependencies (run once)

```bash
# Backend
cd /home/edgar/Documents/AOSBAckend/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd /home/edgar/Documents/AOSBAckend/frontend
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## 2️⃣ Launch the FastAPI backend (turbo)

```bash
# turbo
cd /home/edgar/Documents/AOSBAckend/backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 3️⃣ Launch the Streamlit UI (turbo)

```bash
# turbo
cd /home/edgar/Documents/AOSBAckend/frontend
streamlit run app.py
```

## 4️⃣ Verify

- Open http://localhost:8501 in your browser.
- The UI should now display data without the “Connection refused” errors.
