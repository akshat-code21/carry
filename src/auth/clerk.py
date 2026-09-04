"""Clerk session-token verification for FastAPI.

Uses the official ``clerk-backend-api`` SDK. Verification is networkless when
``CLERK_JWT_KEY`` (PEM public key) is configured; otherwise it falls back to
fetching JWKS from Clerk's Backend API using the secret key.
"""

import logging

from clerk_backend_api import AuthenticateRequestOptions, Clerk, authenticate_request
from clerk_backend_api.security.types import RequestState
from fastapi import HTTPException, Request, status

from src.config import get_settings

logger = logging.getLogger(__name__)

_client: Clerk | None = None


def get_clerk_client() -> Clerk:
    """Lazily initialised Clerk Backend API client (process-wide singleton)."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.clerk_secret_key:
            raise RuntimeError(
                "CLERK_SECRET_KEY is not set. Authentication is required but not configured."
            )
        _client = Clerk(bearer_auth=settings.clerk_secret_key)
    return _client


class AuthenticationError(HTTPException):
    """Raised when a request carries no valid Clerk session."""

    def __init__(self, reason: str = "unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": reason},
            headers={"WWW-Authenticate": "Bearer"},
        )


def _auth_options(secret_key: str, jwt_key: str | None) -> AuthenticateRequestOptions:
    settings = get_settings()
    return AuthenticateRequestOptions(
        secret_key=secret_key,
        jwt_key=jwt_key,
        authorized_parties=settings.clerk_authorized_parties_list or None,
        accepts_token=["session_token"],
    )


def _reason_name(state: RequestState) -> str:
    """Enum-member name of the failure reason (reason may be one of two enum
    types depending on where verification failed)."""
    reason = getattr(state, "reason", None)
    return getattr(reason, "name", "") if reason is not None else ""


def _log_rejected_token_kid(token: str) -> None:
    """Log the unverified JWT header kid - it encodes the Clerk instance that
    signed the token (kid == 'ins_<instance_id>'), which instantly reveals
    frontend/backend instance mismatches."""
    try:
        import jwt as pyjwt

        header = pyjwt.get_unverified_header(token)
        logger.warning(
            "Rejected token header: kid=%s alg=%s - kid must start with this "
            "instance's id (see 'jwk_kid_mismatch' => token from a different "
            "Clerk instance; restart frontend + clear cookies)",
            header.get("kid"),
            header.get("alg"),
        )
    except Exception:  # noqa: BLE001 - diagnostics must never raise
        pass


async def get_clerk_user_profile(clerk_user_id: str) -> dict | None:
    """Fetch a user's profile from the Clerk Backend API.

    Returns {email, full_name, image_url, public_metadata} or None on failure.
    Used because default Clerk session tokens carry no profile claims -
    only ``sub``. One HTTP round-trip; callers must throttle.
    """
    try:
        client = get_clerk_client()
        user = await client.users.get_async(user_id=clerk_user_id)

        email = None
        primary_id = getattr(user, "primary_email_address_id", None)
        for addr in getattr(user, "email_addresses", None) or []:
            if getattr(addr, "id", None) == primary_id:
                email = getattr(addr, "email_address", None)
                break
        if email is None and user.email_addresses:
            email = user.email_addresses[0].email_address

        meta = getattr(user, "public_metadata", None) or {}
        first = getattr(user, "first_name", None)
        last = getattr(user, "last_name", None)
        full_name = " ".join(filter(None, [first, last])) or None
        return {
            "email": email,
            "full_name": full_name,
            "image_url": getattr(user, "image_url", None),
            "public_metadata": meta if isinstance(meta, dict) else {},
        }
    except Exception:
        logger.warning("Failed to fetch Clerk profile for %s", clerk_user_id, exc_info=True)
        return None


def verify_session_token(request: Request) -> dict:
    """Verify the Clerk session token on ``request`` and return its JWT claims.

    Raises :class:`AuthenticationError` (401) when missing/invalid/unconfigured.
    The claims include ``sub`` (the Clerk user id) and optionally profile
    fields exposed via a customised session token template.

    Verification strategy: if ``CLERK_JWT_KEY`` (static PEM) is configured we
    try it first (networkless), but on signature failure we automatically
    fall back to JWKS - Clerk rotates signing keys whenever the session
    token template changes, which would otherwise brick static-PEM setups.

    Note: ``state.reason`` may hold either ``AuthErrorReason`` or
    ``TokenVerificationErrorReason`` depending on where verification failed,
    so comparisons use the enum member *name* rather than identity.
    """
    settings = get_settings()
    if not settings.clerk_secret_key:
        logger.error(
            "Rejected request: authentication required but CLERK_SECRET_KEY is not configured."
        )
        raise AuthenticationError("Server authentication is not configured")

    # Bearer-only. The SDK would otherwise silently fall back to the
    # ``__session`` cookie, which can hold a token minted by a *previously
    # used* Clerk instance (common while switching instances locally) and
    # fails verification with ``jwk_kid_mismatch``. Our API client always
    # sends ``Authorization: Bearer <session token>``, so requiring the
    # header is both safer and deterministic.
    auth_header = request.headers.get("Authorization") or ""
    if not auth_header.startswith("Bearer ") or len(auth_header) <= 7:
        logger.debug("Rejected request without Authorization bearer header")
        raise AuthenticationError("Missing bearer token")

    state: RequestState | None = None
    if settings.clerk_jwt_key:
        state = authenticate_request(
            request, _auth_options(settings.clerk_secret_key, settings.clerk_jwt_key)
        )
        if not state.is_signed_in and _reason_name(state) == "TOKEN_INVALID_SIGNATURE":
            logger.warning(
                "CLERK_JWT_KEY failed to verify a session token (stale key after "
                "Clerk rotation?). Falling back to JWKS - consider removing "
                "CLERK_JWT_KEY from .env so JWKS is used directly."
            )
            state = None  # retry via JWKS below

    if state is None:
        state = authenticate_request(request, _auth_options(settings.clerk_secret_key, None))

    if not state.is_signed_in:
        reason = _reason_name(state) or "unauthorized"
        if reason == "SESSION_TOKEN_MISSING":
            logger.debug("Rejected request without session token")
        else:
            logger.warning("Session token verification failed: %s", reason.lower())
            if reason in ("JWK_KID_MISMATCH", "TOKEN_INVALID_SIGNATURE"):
                token = getattr(state, "token", None)
                if token:
                    _log_rejected_token_kid(token)
        raise AuthenticationError(reason)

    return dict(state.payload or {})
