from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponsePermanentRedirect
from django.utils._os import safe_join
from django.core.exceptions import SuspiciousFileOperation


DOCS_ROOT = Path(settings.BASE_DIR) / "static" / "docs"


def _resolve_resource(resource: str | None) -> Path:
    resource = (resource or "").strip("/")
    if not resource:
        resource = "index.html"

    try:
        resolved = Path(safe_join(str(DOCS_ROOT), resource))
    except SuspiciousFileOperation as exc:  # pragma: no cover - guard clause
        raise Http404("Файл не найден") from exc

    if resolved.is_dir():
        resolved = resolved / "index.html"

    if not resolved.exists():
        raise Http404("Файл не найден")

    return resolved


def docs_serve(request, resource: str | None = None):
    """Вернуть статический файл документации, собранный MkDocs."""

    if (resource is None or resource == "") and not request.path.endswith("/"):
        full_path = request.get_full_path()
        if "?" in full_path:
            path, query = full_path.split("?", 1)
            return HttpResponsePermanentRedirect(f"{path.rstrip('/')}/?{query}")
        return HttpResponsePermanentRedirect(f"{full_path.rstrip('/')}/")

    file_path = _resolve_resource(resource)
    content_type, _ = mimetypes.guess_type(str(file_path))

    response = FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")
    response["Cache-Control"] = "public, max-age=3600"
    return response

