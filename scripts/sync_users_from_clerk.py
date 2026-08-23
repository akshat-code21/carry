#!/usr/bin/env python3
"""Reconcile app-side users with Clerk (source of truth).

- Deletes app user rows whose Clerk account no longer exists.
- Repairs placeholder emails (@unknown.invalid) from the Clerk profile.

Usage:
    PYTHONPATH=. uv run python scripts/sync_users_from_clerk.py [--dry-run]
"""

import argparse
import asyncio

from src.config import get_settings


def fetch_all_clerk_users(sdk) -> dict[str, dict]:
    """Paginate Clerk users; return {clerk_user_id: {email, full_name}}."""
    from clerk_backend_api.models import GetUserListRequest

    users: dict[str, dict] = {}
    limit, offset = 200, 0
    while True:
        batch = sdk.users.list(request=GetUserListRequest(limit=limit, offset=offset))
        for cu in batch:
            email = None
            for addr in cu.email_addresses or []:
                if addr.id == cu.primary_email_address_id:
                    email = addr.email_address
                    break
            email = email or (cu.email_addresses[0].email_address if cu.email_addresses else None)
            users[cu.id] = {
                "email": email,
                "full_name": " ".join(filter(None, [cu.first_name, cu.last_name])) or None,
            }
        if len(batch) < limit:
            break
        offset += limit
    return users


async def main(dry_run: bool) -> None:
    from clerk_backend_api import Clerk
    from sqlalchemy import select

    from src.database import async_session_factory
    from src.models.user import User

    settings = get_settings()
    if not settings.clerk_secret_key:
        print("✗ CLERK_SECRET_KEY not set in .env")
        return

    sdk = Clerk(bearer_auth=settings.clerk_secret_key)
    clerk_users = fetch_all_clerk_users(sdk)
    print(f"Clerk instance has {len(clerk_users)} users")

    deleted, repaired = 0, 0
    async with async_session_factory() as db:
        rows = (await db.execute(select(User))).scalars().all()
        print(f"App database has {len(rows)} users\n")

        for u in rows:
            profile = clerk_users.get(u.clerk_user_id)

            if profile is None:
                if dry_run:
                    print(
                        f"  [dry-run] would DELETE {u.email} ({u.clerk_user_id}) — gone from Clerk"
                    )
                else:
                    await db.delete(u)
                    print(f"  ✓ deleted {u.email} ({u.clerk_user_id}) — gone from Clerk")
                deleted += 1
                continue

            if u.email.endswith("@unknown.invalid") and profile["email"]:
                new_email = profile["email"]
                if dry_run:
                    print(f"  [dry-run] would repair {u.clerk_user_id}: {u.email} -> {new_email}")
                else:
                    u.email = profile["email"].lower()
                    if profile["full_name"] and not u.full_name:
                        u.full_name = profile["full_name"]
                    print(f"  ✓ repaired {u.clerk_user_id}: -> {u.email}")
                repaired += 1

        if not dry_run:
            await db.commit()

    print(f"\nDone. {deleted} deleted, {repaired} repaired" + (" (dry run)" if dry_run else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync app users with Clerk")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
