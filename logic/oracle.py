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
        "If you cannot generate a diagram, output 'ERROR: SYNTHESIS_FAILURE'."
    )
    
    SUMMARIZE_SYSTEM = (
        "You are the AEGIS INTELLIGENCE EXTRACTOR. "
        "Summarize the provided Markdown document into a high-density, technical brief. "
        "Use bullet points. Focus on key technical specifications and operational data. "
        "Tone: Industrial, concise, sci-fi traveller. "
        "Language: Match the language of the source document. "
        "Output ONLY the summary in Markdown format. No filler."
    )
    
    GHOST_SYSTEM = (
        "You are the AEGIS NEURAL HINT system. "
        "Your goal is to provide a brief, professional continuation of the user's document. "
        "RULES: "
        "- COMPLETE THE CURRENT SENTENCE gracefully. "
        "- YOU MAY ADD 1 EXTRA CONCISE, TECHNICAL SENTENCE to follow up. "
        "- LIMIT: 1-2 sentences total. "
        "- NO INTRODUCTIONS, NO CHAT, NO FILLER. "
        "- Tone: Industrial, technical, sci-fi traveller. "
        "- Language: Use the same language as the provided context."
    )

class OracleClient:
    """Industrial Client for the Neural Layer (Ollama)."""
    
    def __init__(self, url: Optional[str] = None, model: Optional[str] = None):
        self.url = url or os.getenv("OLLAMA_URL", "http://172.31.112.1:11434")
        self.model = model or os.getenv("ORACLE_MODEL", "qwen2.5-coder:7b")
        self.client = httpx.AsyncClient(
            timeout=120.0, # Increased for deep synthesis
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def shutdown(self):
        await self.client.aclose()

    async def stream_completion(self, prompt: str, system: Optional[str] = None, options: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Streams neural completion tokens to the caller."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        try:
            async with self.client.stream("POST", f"{self.url}/api/generate", json=payload) as response:
                if response.status_code != 200:
                    raise OracleError(f"NEURAL_LINK_FAILED: {response.status_code}")

                async for line in response.aiter_lines():
                    if not line: continue
                    data = json.loads(line)
                    if token := data.get("response"):
                        yield token
                    if data.get("done"):
                        break
        except Exception as e:
            yield f"ERROR_NEURAL_UPLINK: {str(e)}"

    async def generate_syntax(self, description: str) -> str:
        """Produces Mermaid syntax from natural language inputs."""
        response = await self.client.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": description,
                "system": PromptTemplates.MERMAID_SYSTEM,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            raise OracleError(f"SYNTHESIS_OFFLINE: {response.status_code}")
        
        try:
            data = response.json()
            return data.get("response", "").strip()
        except Exception:
            raise OracleError("DATA_CORRUPTION")

    async def summarize(self, content: str) -> str:
        """Condenses archives into high-density insights."""
        response = await self.client.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": content,
                "system": PromptTemplates.SUMMARIZE_SYSTEM,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            raise OracleError(f"INTELLIGENCE_LINK_FAILED: {response.status_code}")
        
        try:
            data = response.json()
            return data.get("response", "").strip()
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
