import httpx
import os
import json
from typing import AsyncGenerator, Optional

# AEGIS_ORACLE_PROTOCOL: Tactical Neural Interface
class OracleError(Exception):
    """Base exception for Aegis Oracle failures."""
    pass

class PromptTemplates:
    """Centralized prompt vault for tactical consistency."""
    
    MERMAID_SYSTEM = (
        "You are the AEGIS NEURAL SYNTHESIZER. "
        "Convert the user's description into valid Mermaid.js syntax. "
        "Output ONLY the Mermaid code block content. "
        "Do not include markdown code fences (```). "
        "Do not include any introductions, explanations, or conversational filler. "
        "CRITICAL RULES: "
        "- ALWAYS use double quotes around node labels: e.g. A[\"Label (Info)\"] "
        "- This is mandatory for multi-word labels or those containing brackets/commas. "
        "If you cannot generate a diagram, output 'ERROR: SYNTHESIS_FAILURE'."
    )
    
    SUMMARIZE_SYSTEM = (
        "You are the AEGIS INTELLIGENCE EXTRACTOR. "
        "Summarize the provided Archive ([SOURCE_DOCUMENT]) into a high-density, technical brief. "
        "Use bullet points. Focus on key technical specifications and operational data. "
        "Tone: Industrial, concise, sci-fi traveller. "
        "Language: Use the same language as the provided source document. "
        "Output ONLY the summary in Markdown format. No filler."
    )
    
    GHOST_SYSTEM = (
        "You are the AEGIS NEURAL HINT system. "
        "Your goal is to provide a seamless, professional continuation of the provided text. "
        "CRITICAL RULES: "
        "- DO NOT REPEAT ANY PART OF THE PROVIDED CONTEXT. "
        "- START IMMEDIATELY with the characters or sentence needed to continue. "
        "- FINISH THE CURRENT THOUGHT FULLY and gracefully. "
        "- YOU MAY ADD 1-2 EXTRA TECHNICAL SENTENCES to expand the insight. "
        "- LIMIT: 3-4 sentences total. "
        "- NO INTRODUCTIONS, NO CHAT, NO FILLER. "
        "- Language: Use the same language as the provided context."
    )

from logic.settings import settings

class OracleClient:
    """Industrial Client for the Neural Layer (Ollama)."""

    def __init__(self):
        self._url = None
        self._models = {}
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=600.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    def _get_config(self) -> tuple[str, dict]:
        """Dynamically retrieves latest parameters from the core buffer."""
        if not settings.get("neural_link_enabled", True):
            raise OracleError("NEURAL_PROTOCOL_OFFLINE")
        return settings.get("ollama_ip"), settings.get("models")

    async def probe_url(self) -> None:
        """Validates the configured Neural Core endpoint on startup."""
        try:
            url, _ = self._get_config()
            async with httpx.AsyncClient(timeout=2.0) as probe_client:
                r = await probe_client.get(f"{url}/api/tags")
                if r.status_code == 200:
                    self._url = url
        except Exception:
            self._url = None
            pass # Connection errors handled on request
        except Exception:
            pass # Fails silently, connection errors will be handled during actual requests

    async def shutdown(self):
        await self.client.aclose()

    async def stream_completion(self, prompt: str, system: Optional[str] = None, options: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Streams neural completion tokens using hint model."""
        url, models = self._get_config()
        payload = {
            "model": models.get("neural_hint"),
            "prompt": prompt,
            "stream": True
        }
        if system: payload["system"] = system
        if options: payload["options"] = options

        try:
            async with self.client.stream("POST", f"{url}/api/generate", json=payload) as response:
                if response.status_code != 200:
                    raise OracleError(f"NEURAL_LINK_FAILED: {response.status_code}")
                async for line in response.aiter_lines():
                    if not line: continue
                    data = json.loads(line)
                    if token := data.get("response"): yield token
                    if data.get("done"): break
        except Exception as e:
            yield f"ERROR_NEURAL_UPLINK: {str(e)}"

    async def generate_syntax(self, description: str) -> str:
        """Produces Mermaid syntax from synthesis model."""
        url, models = self._get_config()
        try:
            response = await self.client.post(
                f"{url}/api/generate",
                json={
                    "model": models.get("mermaid_synthesis"),
                    "prompt": description,
                    "system": PromptTemplates.MERMAID_SYSTEM,
                    "stream": False
                }
            )
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            raise OracleError("NEURAL_CORE_UNREACHABLE") from exc
        except httpx.TimeoutException as exc:
            raise OracleError("NEURAL_INFERENCE_TIMEOUT") from exc

        if response.status_code != 200:
            raise OracleError(f"SYNTHESIS_OFFLINE: {response.status_code}")

        try:
            return response.json().get("response", "").strip()
        except Exception:
            raise OracleError("DATA_CORRUPTION")

    async def summarize(self, content: str) -> str:
        """Condenses archives using scan model."""
        url, models = self._get_config()
        try:
            response = await self.client.post(
                f"{url}/api/generate",
                json={
                    "model": models.get("neural_scan"),
                    "prompt": f"[SOURCE_DOCUMENT_START]\n---\n{content}\n---\n[SOURCE_DOCUMENT_END]\n[TASK]: Perform full intelligence scan and provide technical summary.",
                    "system": PromptTemplates.SUMMARIZE_SYSTEM,
                    "stream": False,
                    "options": {
                        "num_ctx": 16384,
                        "num_predict": 1000,
                        "temperature": 0.2
                    }
                }
            )
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            raise OracleError("NEURAL_CORE_UNREACHABLE") from exc
        except httpx.TimeoutException as exc:
            raise OracleError("NEURAL_INFERENCE_TIMEOUT") from exc

        if response.status_code != 200:
            raise OracleError(f"INTELLIGENCE_LINK_FAILED: {response.status_code}")

        try:
            return response.json().get("response", "").strip()
        except Exception:
            raise OracleError("BUFFER_OVERFLOW")

# Global instance for app lifecycle management
oracle = OracleClient()

# Legacy Compatibility Wrappers
async def generate_completion(p, s=None):
    async for t in oracle.stream_completion(p, s):
        yield t

async def generate_mermaid(d):
    try:
        return await oracle.generate_syntax(d)
    except OracleError as e:
        return f"ERROR: {str(e)}"

async def summarize_document(c):
    try:
        return await oracle.summarize(c)
    except OracleError as e:
        return f"ERROR: {str(e)}"
