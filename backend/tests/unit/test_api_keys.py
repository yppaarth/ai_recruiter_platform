import json
import os
from pathlib import Path

import httpx
import pytest
from dotenv import dotenv_values

from app.services.grok_client import GrokClient


@pytest.mark.asyncio
async def test_grok_client_sends_configured_api_key(httpx_mock):
    client = GrokClient()
    client.api_key = "configured-test-key"
    client.base_url = "https://api.x.ai/v1"
    client.model = "grok-test"
    client.headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
    }

    httpx_mock.add_response(
        method="POST",
        url="https://api.x.ai/v1/chat/completions",
        json={"choices": [{"message": {"content": "ok"}}]},
    )

    result = await client._chat_completion(
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1,
    )

    request = httpx_mock.get_request()
    assert result == "ok"
    assert request.headers["Authorization"] == "Bearer configured-test-key"
    assert request.headers["Content-Type"] == "application/json"

    payload = json.loads(request.content)
    assert payload["model"] == "grok-test"
    assert payload["messages"] == [{"role": "user", "content": "ping"}]


@pytest.mark.asyncio
async def test_grok_client_invalid_api_key_response_fails(httpx_mock):
    client = GrokClient()
    client.api_key = "invalid-test-key"
    client.base_url = "https://api.x.ai/v1"
    client.headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
    }

    httpx_mock.add_response(
        method="POST",
        url="https://api.x.ai/v1/chat/completions",
        status_code=401,
        json={"error": {"message": "invalid api key"}},
    )

    with pytest.raises(httpx.HTTPStatusError) as exc:
        await client._chat_completion(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )

    assert exc.value.response.status_code == 401


@pytest.mark.asyncio
async def test_live_grok_api_key_when_explicitly_enabled():
    if os.getenv("RUN_LIVE_GROK_API_TEST") != "1":
        pytest.skip("Set RUN_LIVE_GROK_API_TEST=1 to test the real Grok API key.")

    repo_root = Path(__file__).resolve().parents[3]
    env_values = dotenv_values(repo_root / ".env")
    api_key = os.getenv("GROK_API_KEY") or env_values.get("GROK_API_KEY")

    if not api_key or api_key in {"test-key", "your_grok_api_key_here"}:
        pytest.fail("Set a real GROK_API_KEY in .env before running the live test.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": os.getenv("GROK_MODEL") or env_values.get("GROK_MODEL") or "grok-4.3",
        "messages": [{"role": "user", "content": "Reply with only: ok"}],
        "max_tokens": 5,
        "temperature": 0,
    }
    base_url = os.getenv("GROK_BASE_URL") or env_values.get("GROK_BASE_URL") or "https://api.x.ai/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    assert response.status_code == 200, response.text
    assert response.json()["choices"][0]["message"]["content"]
