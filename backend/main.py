import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

#import nest_asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nemoguardrails import LLMRails, RailsConfig

#nest_asyncio.apply()

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(os.getenv("NEMO_CONFIG_DIR", BASE_DIR / "config"))
CATALOG_PATH = Path(os.getenv("CATALOG_PATH", BASE_DIR / "product_catalog_visual_products.json"))
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

UNSAFE_RESPONSE = (
    "I'm sorry, I can't help with that request. "
    "I'll refer you to one of our customer service agents. Please wait."
)

DEFAULT_REFUSAL_PHRASES = [
    "I'm sorry, I can't respond to that.",
    "i'm sorry i can't answer that",
    "i am sorry, i can't answer that",
    "i'm sorry, but i can't answer that",
    "i can't help with that",
    "i cannot help with that",
]


def replace_refusal_message(answer: str) -> str:
    normalized_answer = answer.strip().lower()

    for phrase in DEFAULT_REFUSAL_PHRASES:
        if phrase in normalized_answer:
            return UNSAFE_RESPONSE

    return answer

SYSTEM_PROMPT = """
You are Agrobot, an agriculture e-commerce assistant.
""".strip()

app = FastAPI(title="AgroGuard Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryMessage(BaseModel):
    role: str
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[HistoryMessage] = []
    top_k: int = Field(3, ge=1, le=8)

class ChatResponse(BaseModel):
    answer: str
    retrieved_context: List[str]

rails: LLMRails | None = None
embedding_model: SentenceTransformer | None = None
documents: List[str] = []
document_embeddings = None


def load_catalog() -> List[str]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Catalog file not found at {CATALOG_PATH}. Put product_catalog_visual_products.json there "
            "or set CATALOG_PATH in .env."
        )

    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        products = json.load(f)

    docs: List[str] = []
    for product in products:
        text = f"""
Product ID: {product.get("product_id", "")}
Product Name: {product.get("product_name", "")}
Product Type: {product.get("product_type", "")}
Usage: {product.get("usage", "")}
Dosage: {product.get("dosage", "")}
Applicable Crops: {product.get("applicable_crops", "")}
Ingredients: {product.get("ingredients", "")}
Application Method: {product.get("application_method", "")}
""".strip()
        docs.append(text)
    return docs


@app.on_event("startup")
def startup() -> None:
    global rails, embedding_model, documents, document_embeddings

    if not CONFIG_DIR.exists():
        raise FileNotFoundError(
            f"NeMo Guardrails config folder not found at {CONFIG_DIR}. Copy your ./config folder here "
            "or set NEMO_CONFIG_DIR in .env."
        )

    documents = load_catalog()
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    document_embeddings = embedding_model.encode(
        documents,
        convert_to_tensor=False,
        normalize_embeddings=True,
    )

    config = RailsConfig.from_path(str(CONFIG_DIR))
    rails = LLMRails(config)


def retrieve_products(question: str, top_k: int = 3) -> List[str]:
    if embedding_model is None or document_embeddings is None:
        raise RuntimeError("Embedding model is not ready.")

    question_embedding = embedding_model.encode(
        [question],
        convert_to_tensor=False,
        normalize_embeddings=True,
    )
    scores = cosine_similarity(question_embedding, document_embeddings)[0]
    top_indices = scores.argsort()[-top_k:][::-1]
    return [documents[i] for i in top_indices]


def build_messages(
    user_message: str,
    context: str,
    history: List[HistoryMessage] | None = None,
) -> List[Dict[str, str]]:
    conversation_history: List[Dict[str, str]] = []

    for item in history or []:
        if item.role in {"user", "assistant"}:
            conversation_history.append(
                {
                    "role": item.role,
                    "content": item.content,
                }
            )

    # Keep only the most recent messages so the prompt does not get too large.
    conversation_history = conversation_history[-10:]

    catalog_context_message = f"""
Catalog context retrieved for the current user question:

{context}

Use this catalog context as the only source of truth for product information.
If a requested product detail is not present above, say you don't have that information at the moment.
""".strip()

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": catalog_context_message},
        *conversation_history,
        {"role": "user", "content": user_message},
    ]

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "rails_loaded": rails is not None,
        "documents_loaded": len(documents),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if rails is None:
        raise HTTPException(status_code=503, detail="NeMo Guardrails is not ready.")

    retrieved_docs = retrieve_products(request.message, request.top_k)
    messages = build_messages(
        request.message,
        "\n\n".join(retrieved_docs),
        request.history,
    )

    try:
        result = await asyncio.to_thread(rails.generate, messages=messages)

        answer = result.get("content", "No answer returned.")
        answer = replace_refusal_message(answer)

        return ChatResponse(
            answer=answer,
            retrieved_context=retrieved_docs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc