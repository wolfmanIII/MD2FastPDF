"""
AEGIS_EXCEPTION_PROTOCOL: Centralized domain exception hierarchy.

All logic/ modules raise these — HTTP translation happens exclusively
in main.py exception handlers. No FastAPI imports in business logic.
"""


class AegisError(Exception):
    """Base exception for all SC-ARCHIVE domain errors."""
    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


# --- Filesystem Errors ---

class AccessDeniedError(AegisError):
    """Path traversal, hidden path, or permission violation."""
    def __init__(self, detail: str = "ACCESS_DENIED"):
        super().__init__(detail, status_code=403)


class NotFoundError(AegisError):
    """File or directory does not exist."""
    def __init__(self, detail: str = "NOT_FOUND"):
        super().__init__(detail, status_code=404)


class InvalidPathError(AegisError):
    """Malformed or unresolvable path."""
    def __init__(self, detail: str = "INVALID_PATH_FORMAT"):
        super().__init__(detail, status_code=400)


class InvalidFileTypeError(AegisError):
    """Operation attempted on unsupported file type."""
    def __init__(self, detail: str = "INVALID_FILE_TYPE"):
        super().__init__(detail, status_code=400)


class FileConflictError(AegisError):
    """File already exists at target path."""
    def __init__(self, detail: str = "FILE_ALREADY_EXISTS"):
        super().__init__(detail, status_code=400)


class FilenameRequiredError(AegisError):
    """Empty or missing filename."""
    def __init__(self, detail: str = "FILENAME_REQUIRED"):
        super().__init__(detail, status_code=400)


# --- Conversion Errors ---

class ConversionError(AegisError):
    """Gotenberg PDF conversion failure."""
    def __init__(self, detail: str = "CONVERSION_FAILED"):
        super().__init__(detail, status_code=502)


# --- Neural / Oracle Errors ---

class OracleError(AegisError):
    """Aegis Oracle (Ollama) failure."""
    def __init__(self, detail: str = "ORACLE_ERROR"):
        super().__init__(detail, status_code=502)


# --- Render Errors ---

class RenderError(AegisError):
    """Mermaid render pipeline failure."""
    def __init__(self, detail: str = "RENDER_FAILED"):
        super().__init__(detail, status_code=502)
