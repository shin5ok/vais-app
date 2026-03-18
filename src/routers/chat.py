import os
import uuid
from typing import Annotated

import markdown
from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services.search import SearchService

router = APIRouter(prefix="/chat", tags=["chat"])

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

sessions: dict[str, list[dict]] = {}

search_service = SearchService()


def get_session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie("session_id", session_id, httponly=True)
    return session_id


@router.post("", response_class=HTMLResponse)
async def send_message(
    request: Request,
    response: Response,
    message: Annotated[str, Form()],
):
    session_id = get_session_id(request, response)

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({"role": "user", "content": message})

    # 現在のメッセージを除いた履歴を渡す
    history = sessions[session_id][:-1]
    search_result = await search_service.search(message, session_id, history)

    sessions[session_id].append({"role": "assistant", "content": search_result.summary})

    assistant_html = markdown.markdown(
        search_result.summary,
        extensions=["nl2br", "tables", "fenced_code"],
    )

    citations = [{"title": c.title, "uri": c.uri} for c in search_result.citations]

    return templates.TemplateResponse(
        request,
        "partials/message.html",
        {
            "user_message": message,
            "assistant_message": assistant_html,
            "citations": citations,
        },
    )


@router.delete("", response_class=HTMLResponse)
async def clear_chat(request: Request, response: Response):
    session_id = get_session_id(request, response)
    if session_id in sessions:
        del sessions[session_id]
    search_service.clear_session(session_id)
    return HTMLResponse("")
