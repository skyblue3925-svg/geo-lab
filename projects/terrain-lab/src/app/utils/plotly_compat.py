"""Centralized optional plotly imports with graceful fallback."""

PLOTLY_IMPORT_ERROR = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except Exception as exc:
    go = None
    px = None
    make_subplots = None
    PLOTLY_IMPORT_ERROR = exc


def plotly_error_message() -> str:
    """Return a user-facing message when plotly is unavailable."""
    base = "Plotly 모듈을 로드할 수 없습니다."
    if PLOTLY_IMPORT_ERROR is not None:
        return f"{base} 원인: {type(PLOTLY_IMPORT_ERROR).__name__} - {PLOTLY_IMPORT_ERROR}"
    return f"{base} requirements.txt의 환경을 확인하고 서버를 재시작해 주세요."


def require_plotly(context: str = "plotly") -> None:
    """Raise a clear error if plotly is not available."""
    if go is None:
        raise ModuleNotFoundError(f"{context}: {plotly_error_message()}")

