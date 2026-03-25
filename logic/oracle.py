import httpx
import os
import json
from typing import AsyncGenerator, Optional

# AEGIS_ORACLE_CONFIG: Neural layer parameters
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://172.31.112.1:11434")
ORACLE_MODEL = os.getenv("ORACLE_MODEL", "qwen2.5-coder:7b")

# Persistent connection pool for neural synchronization
_http_client = httpx.AsyncClient(
    timeout=60.0, 
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)

async def generate_completion(prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    AEGIS GHOST_TEXT: Streams neural completion tokens to the editor.
    """
    payload = {
        "model": ORACLE_MODEL,
        "prompt": prompt,
        "stream": True
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with _http_client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as response:
        if response.status_code != 200:
            yield f"ERROR_NEURAL_LINK_FAILED: {response.status_code}"
            return

        async for line in response.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
            except json.JSONDecodeError:
                continue

async def generate_mermaid(description: str) -> str:
    """
    AEGIS SYNTHESIS: Converts tactical descriptions into Mermaid.js syntax.
    """
    system_prompt = (
        "You are the AEGIS NEURAL SYNTHESIZER. "
        "Convert the user's description into valid Mermaid.js syntax. "
        "Output ONLY the Mermaid code block content. "
        "Do not include markdown code fences (```). "
        "Do not include any introductions, explanations, or conversational filler. "
        "If you cannot generate a diagram, output 'ERROR: SYNTHESIS_FAILURE'."
    )
    
    response = await _http_client.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": ORACLE_MODEL,
            "prompt": description,
            "system": system_prompt,
            "stream": False
        }
    )
    
    if response.status_code != 200:
        return f"ERROR: NEURAL_LINK_OFFLINE ({response.status_code})"
    
    try:
        data = response.json()
        return data.get("response", "").strip()
    except (json.JSONDecodeError, KeyError):
        return "ERROR: DATA_CORRUPTION"

async def summarize_document(content: str) -> str:
    """
    AEGIS INTELLIGENCE_EXTRACTOR: Condenses archives into high-density insights.
    """
    system_prompt = (
        "You are the AEGIS INTELLIGENCE EXTRACTOR. "
        "Summarize the provided Markdown document into a high-density, technical brief. "
        "Use bullet points. Focus on key technical specifications and operational data. "
        "Tone: Industrial, concise, sci-fi traveller. "
        "Language: Match the language of the source document. "
        "Output ONLY the summary in Markdown format. No filler."
    )
    
    response = await _http_client.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": ORACLE_MODEL,
            "prompt": content,
            "system": system_prompt,
            "stream": False
        }
    )
    
    if response.status_code != 200:
        return f"ERROR: UPLINK_LOST ({response.status_code})"
    
    try:
        data = response.json()
        return data.get("response", "").strip()
    except (json.JSONDecodeError, KeyError):
        return "ERROR: BUFFER_OVERFLOW"
