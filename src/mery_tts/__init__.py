from importlib import metadata

PUBLIC_API_BOUNDARY = "/v1"

try:
    __version__ = metadata.version("mery-tts-server")
except metadata.PackageNotFoundError:  # pragma: no cover - source-tree fallback before install
    __version__ = "0.1.0"

__all__ = ["PUBLIC_API_BOUNDARY", "__version__"]
