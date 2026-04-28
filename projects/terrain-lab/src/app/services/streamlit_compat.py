"""Small compatibility shims for Streamlit API differences."""

from __future__ import annotations

import inspect
from typing import Any


def image_stretch(st_module: Any, image: Any, **kwargs: Any) -> Any:
    """Render an image at container width across old and new Streamlit versions."""
    kwargs.pop("width", None)
    kwargs.pop("use_container_width", None)
    kwargs.pop("use_column_width", None)

    parameters = inspect.signature(st_module.image).parameters
    if "use_container_width" in parameters:
        kwargs["use_container_width"] = True
    elif "use_column_width" in parameters:
        kwargs["use_column_width"] = True

    return st_module.image(image, **kwargs)
