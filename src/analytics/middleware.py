"""Analytics middleware — logs every served API request with latency and user.

Runs inside CORS middleware; skips health checks, docs and preflights.
Reads ``request.state.user_id`` (set by the auth dependency) after the
response completes so requests are attributed to users.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.analytics.service import analytics

# Paths that never get logged (health probes, docs, internal assets)
_EXEMPT_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/health",
)
EXEMPT_PATHS = {"/"}


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not analytics.enabled:
            return await call_next(request)

        path = request.url.path
        if (
            request.method == "OPTIONS"
            or path in EXEMPT_PATHS
            or any(path.startswith(p) for p in _EXEMPT_PREFIXES)
        ):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0

            # Route template collapses ids: /api/videos/{video_id}
            route = request.scope.get("route")
            route_template = getattr(route, "path_format", None) or path

            # user_id is stored on scope state by the auth dependency;
            # unavailable for unauthenticated/exempt routes.
            state = getattr(request.scope, "state", None) or {}
            user_id = state.get("user_id")

            analytics.record_api_request(
                user_id=user_id,
                method=request.method,
                path=path,
                route_template=route_template,
                status_code=status_code,
                duration_ms=duration_ms,
            )
