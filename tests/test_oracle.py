"""Tests for OracleClient.translate_query() (RF-11 step 3).

First tests for logic/oracle.py in this repo — no prior mocking pattern for
Ollama existed (docs/ANALISI-relazioni-query-nl.md §6). Uses httpx.MockTransport,
already a direct dependency of the project, instead of introducing a new one.
"""
import json

import httpx
import pytest

from logic.oracle import OracleClient


class _FakeSettings:
    """Minimal stand-in for config.settings.SettingsManager."""

    def __init__(self, enabled: bool = True, models: dict | None = None):
        self._enabled = enabled
        self._models = models if models is not None else {"neural_query": "llama3.2"}

    def get(self, key, default=None):
        if key == "neural_link_enabled":
            return self._enabled
        if key == "ollama_ip":
            return "http://fake-ollama:11434"
        if key == "models":
            return self._models
        return default


def _client_with_transport(handler, enabled: bool = True) -> OracleClient:
    oracle = OracleClient(_FakeSettings(enabled=enabled))
    oracle.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return oracle


@pytest.mark.anyio
async def test_valid_json_response_is_parsed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": json.dumps({
            "intent": "relation_query", "entity": "Kira Venn", "relation": "hostile_to"
        })})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("chi è ostile a Kira Venn?")
    assert result == {"intent": "relation_query", "entity": "Kira Venn", "relation": "hostile_to"}


@pytest.mark.anyio
async def test_json_surrounded_by_prose_is_extracted():
    def handler(request: httpx.Request) -> httpx.Response:
        raw = 'Ecco il risultato: {"intent": "unresolved"} spero sia utile.'
        return httpx.Response(200, json={"response": raw})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualcosa di ambiguo")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_non_200_response_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model not found"})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_unparseable_response_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "questo non è JSON valido"})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_malformed_json_object_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": '{"intent": "relation_query", '})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_non_dict_json_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "[1, 2, 3]"})

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_connection_error_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_timeout_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    oracle = _client_with_transport(handler)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}


@pytest.mark.anyio
async def test_neural_link_disabled_is_unresolved():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should never reach the network when disabled")

    oracle = _client_with_transport(handler, enabled=False)
    result = await oracle.translate_query("qualsiasi cosa")
    assert result == {"intent": "unresolved"}
