import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .gigachat_client import GigaChatClient
from .models import ChatRequest, ChatResponse
from .service import ChatService


load_dotenv()


app = FastAPI(
    title="Negotiation Chat Service",
    version="1.0.0",
)


# Разрешаем тестовый UI на порту 5500
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_service() -> ChatService:

    credentials = os.getenv(
        "GIGACHAT_CREDENTIALS"
    )

    if not credentials:
        raise RuntimeError(
            "GIGACHAT_CREDENTIALS is not configured."
        )

    scope = os.getenv(
        "GIGACHAT_SCOPE",
        "GIGACHAT_API_PERS",
    )

    model = os.getenv(
        "GIGACHAT_MODEL",
        "GigaChat-2-Pro",
    )

    verify_ssl_certs = (
        os.getenv(
            "GIGACHAT_VERIFY_SSL_CERTS",
            "false",
        ).lower()
        == "true"
    )

    client = GigaChatClient(
        credentials=credentials,
        scope=scope,
        model=model,
        verify_ssl_certs=verify_ssl_certs,
    )

    return ChatService(client)


service = create_service()


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/chat/message",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
):

    try:
        return service.process_message(request)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )