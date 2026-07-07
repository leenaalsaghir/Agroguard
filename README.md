# AgroGuardAI

AgroGuardAI is an agriculture-focused chatbot that answers customer questions about agricultural products using a local product catalog, retrieval, a locally served Ollama model, and NeMo Guardrails safety checks.

The system has three main parts:

1. **Ollama model server** - runs the local LLM on port `11434`
2. **FastAPI backend** - handles RAG retrieval, NeMo Guardrails, and API requests
3. **React/Vite frontend** - provides the chat interface

---

## Project Structure

```text
agroguard-final/
  backend/
    main.py
    requirements.txt
    product_catalog_visual_products.json
    config/
      config.yml
      prompts.yml
      rails.co

  frontend/
    index.html
    package.json
    vite.config.js
    public/
      agrobot.png
      favicon.svg
      icons.svg
    src/
      main.jsx
      App.jsx
      components/
        ChatScreen.jsx
      services/
        api.js
      styles/
        index.css
        chat.css
```

---

## Prerequisites

Install these before running the project:

- Python 3.11 or 3.12
- Node.js and npm
- Ollama
- A local Ollama model named `agroguard-qwen`
- NVIDIA API key for the NeMo Guardrails content safety model

---

## 1. Start Ollama

Open a terminal and run:

```bash
ollama serve
```

Keep this terminal running.

In another terminal, confirm that your model exists:

```bash
ollama list
```

The backend config expects this model name:

```text
agroguard-qwen
```

You can test the model with:

```bash
ollama run agroguard-qwen
```

If your Ollama model has a different name, update this field in `backend/config/config.yml`:

```yaml
models:
  - type: main
    engine: openai
    model: agroguard-qwen
    parameters:
      base_url: http://localhost:11434/v1
      api_key: ollama
```

---

## 2. Set Up the Backend

Open a new terminal:

```bash
cd agroguard-final/backend
```

Create and activate a virtual environment:

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Add the NVIDIA API Key

The project uses NeMo Guardrails content safety checks, so the backend needs an NVIDIA API key.

### macOS / Linux

```bash
export NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
```

### Windows PowerShell

```powershell
$env:NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
```

Keep this terminal open after setting the key.

---

## 4. Start the Backend

From the `backend` folder, run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

The frontend currently defaults to this backend URL:

```text
http://127.0.0.1:8081
```

Test the backend health endpoint:

```text
http://127.0.0.1:8081/health
```

Expected response format:

```json
{
  "status": "ok",
  "rails_loaded": true,
  "documents_loaded": 123
}
```

The exact `documents_loaded` number depends on the product catalog file.

---

## 5. Set Up the Frontend

Open a new terminal:

```bash
cd agroguard-final/frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Open the Vite URL, usually:

```text
http://localhost:5173
```

---

## 6. Optional Frontend Environment Variable

The frontend already defaults to:

```text
http://127.0.0.1:8081
```

If you want to set it manually, create a `.env` file inside `frontend/`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8081
```

Then restart the frontend.

---

## 7. Normal Startup Order

Use this order every time you run the project:

### Terminal 1 - Ollama

```bash
ollama serve
```

### Terminal 2 - Backend

```bash
cd agroguard-final/backend
.venv\Scripts\activate
$env:NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

For macOS/Linux, use:

```bash
cd agroguard-final/backend
source .venv/bin/activate
export NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

### Terminal 3 - Frontend

```bash
cd agroguard-final/frontend
npm run dev
```
---

## Important Notes

- The local LLM is served through Ollama.
- Ollama runs on `http://localhost:11434`.
- NeMo Guardrails connects to Ollama through the OpenAI-compatible endpoint `http://localhost:11434/v1`.
- The backend retrieves product information from `product_catalog_visual_products.json`.
- The assistant should not invent product names, dosages, ingredients, safety claims, or application methods.
- The frontend connects to the backend at `http://127.0.0.1:8081` unless `VITE_API_BASE_URL` is changed.

---

## Troubleshooting

### Frontend says it cannot connect to AgroGuardAI

Make sure the backend is running on port `8081`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

Also check:

```text
http://127.0.0.1:8081/health
```

### Backend cannot connect to the model

Make sure Ollama is running:

```bash
ollama serve
```

Then check that the model exists:

```bash
ollama list
```

The model name should match `backend/config/config.yml`.

### NeMo Guardrails safety check fails

Make sure the NVIDIA API key is set in the same terminal where you run the backend:

```powershell
$env:NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
```

or:

```bash
export NVIDIA_API_KEY="paste_your_nvidia_api_key_here"
```

### CORS or frontend URL issue

The backend allows the frontend origin:

```text
http://localhost:5173
```

If Vite opens on a different port, either restart Vite on port `5173` or update `FRONTEND_ORIGIN` in the backend environment.
