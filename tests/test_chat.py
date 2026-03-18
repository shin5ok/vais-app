import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.services.search import SearchService


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


async def test_index(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "Vertex AI Search" in response.text


async def test_chat_post(client: AsyncClient):
    response = await client.post(
        "/chat",
        data={"message": "Hello"},
    )
    assert response.status_code == 200
    assert "Hello" in response.text


async def test_chat_post_contains_citations(client: AsyncClient):
    response = await client.post(
        "/chat",
        data={"message": "Test query"},
    )
    assert response.status_code == 200
    assert "citations" in response.text
    assert "参照元" in response.text
    assert "https://example.com/doc1" in response.text


async def test_chat_delete(client: AsyncClient):
    response = await client.delete("/chat")
    assert response.status_code == 200


def test_convert_gs_to_https():
    service = SearchService()

    # gs:// -> https://storage.googleapis.com/
    assert service._convert_gs_to_https("gs://bucket/path/file.pdf") == \
        "https://storage.googleapis.com/bucket/path/file.pdf"

    # https:// はそのまま
    assert service._convert_gs_to_https("https://example.com/doc") == \
        "https://example.com/doc"

    # 空文字
    assert service._convert_gs_to_https("") == ""
