#!/usr/bin/env python3
"""Provision pilot users with credentials YOU choose.

For each user in a CSV (name,email[,password]):
  1. Creates a verified Clerk account. Uses the password from the CSV if
     given (min 8 chars), otherwise generates a strong random one.
     If the Clerk user already exists, a provided password RESETS it.
  2. Creates an ACTIVE app-side User row — so they skip the invite gate.
  3. Writes a credential sheet CSV you can send to each person.

They can log in with the emailed credentials OR "Continue with Google"
using the same email (accounts auto-link on first Google sign-in).

All provisioned users are regular users. To make someone an admin, set
their public metadata in the Clerk dashboard:
    Users → <user> → Metadata → Public metadata → {"role": "admin"}

Usage:
    PYTHONPATH=. uv run python scripts/provision_pilot_users.py users.csv \
        [--out credentials.csv] [--login-url http://localhost:3000/sign-in]

users.csv format (header optional):
    Akshat,akshat@example.com,SuperSecret123
    Jane,jane@example.com
"""

import argparse
import asyncio
import csv
import secrets
import sys
from pathlib import Path

from src.config import get_settings


def parse_rows(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for i, raw in enumerate(csv.reader(fh)):
            if not raw or not raw[0].strip():
                continue
            cells = [c.strip() for c in raw]
            # Skip header row like name,email[,password]
            if i == 0 and cells[1].lower() == "email":
                continue
            if len(cells) < 2 or "@" not in cells[1]:
                print(f"  ! skipping malformed line {i + 1}: {raw}")
                continue
            name_part = cells[0]
            if " " in name_part:
                first, _, last = name_part.partition(" ")
            else:
                first, last = name_part, ""
            password = cells[2] if len(cells) > 2 and cells[2] else None
            if password is not None and len(password) < 8:
                print(
                    f"  ! skipping {cells[1]}: password must be at least 8 characters"
                )
                continue
            rows.append(
                {
                    "first_name": first,
                    "last_name": last,
                    "email": cells[1].lower(),
                    "password": password,
                }
            )
    return rows


def generate_password() -> str:
    """Clerk requires ≥8 chars; this yields 16 with mixed classes."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(16))


async def upsert_app_user(
    session_factory,
    *,
    clerk_user_id: str,
    email: str,
    full_name: str | None,
) -> None:
    from sqlalchemy import func, select

    from src.models.user import User, UserStatus

    async with session_factory() as db:
        existing = (
            await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
        ).scalar_one_or_none()
        if existing is None:
            existing = (
                await db.execute(select(User).where(func.lower(User.email) == email.lower()))
            ).scalar_one_or_none()
        if existing is None:
            existing = User(
                clerk_user_id=clerk_user_id,
                email=email.lower(),
                full_name=full_name,
                status=UserStatus.ACTIVE,
                signup_method="pre_provisioned",
            )
            db.add(existing)
        else:
            existing.clerk_user_id = clerk_user_id
            existing.status = UserStatus.ACTIVE
        await db.commit()


async def provision(rows: list[dict], out_path: str | None, login_url: str) -> int:
    from clerk_backend_api import Clerk
    from clerk_backend_api.models import GetUserListRequest

    from src.database import async_session_factory

    settings = get_settings()
    if not settings.clerk_secret_key:
        print("✗ CLERK_SECRET_KEY not set in .env")
        return 1

    sdk = Clerk(bearer_auth=settings.clerk_secret_key)
    results: list[dict] = []
    failures = 0

    for row in rows:
        email = row["email"]
        display = f"{row['first_name']} {row['last_name']}".strip()
        custom_password = row["password"]

        # Idempotency: reuse an existing Clerk user with this verified email
        try:
            found = sdk.users.list(request=GetUserListRequest(email_address=[email]))
            clerk_user = found[0] if found else None
        except Exception:
            clerk_user = None

        password: str | None = None
        password_note = ""
        try:
            if clerk_user is None:
                password = custom_password or generate_password()
                clerk_user = sdk.users.create(
                    first_name=row["first_name"] or None,
                    last_name=row["last_name"] or None,
                    email_address=[email],
                    password=password,
                )
                print(f"  ✓ created Clerk user {email} ({clerk_user.id})")
            else:
                if custom_password:
                    # Reset the password on the existing account to the custom one
                    sdk.users.update(user_id=clerk_user.id, password=custom_password)
                    password = custom_password
                    password_note = " (password reset)"
                    print(f"  ✓ reset password for existing user {email}")
                else:
                    print(f"  • Clerk user already exists for {email} — password unchanged")
        except Exception as exc:
            failures += 1
            print(f"  ✗ Clerk failed for {email}: {exc}")
            continue

        await upsert_app_user(
            async_session_factory,
            clerk_user_id=clerk_user.id,
            email=email,
            full_name=display or None,
        )

        results.append(
            {
                "name": display,
                "email": email,
                "password": password or "(unchanged)",
                "login_url": login_url,
            }
        )
        if password_note:
            results[-1]["password"] += password_note

    if out_path and results:
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["name", "email", "password", "login_url"]
            )
            writer.writeheader()
            writer.writerows(results)
        print(f"\nCredential sheet written to {out_path} — share each row privately.")

    print("\nSummary:")
    for r in results:
        print(f"  {r['email']:<32} {r['password']}")
    print(
        "\nTell each user:\n"
        f"  1. Sign in at {login_url}\n"
        "  2. Use the email + password above (prefer this), OR\n"
        '  3. Click "Continue with Google" with the SAME email — accounts link automatically.'
    )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision pilot users")
    parser.add_argument("csv", help="CSV file with name,email[,password] rows")
    parser.add_argument("--out", default="credentials.csv", help="Output credentials CSV path")
    parser.add_argument("--login-url", default="http://localhost:3000/sign-in")
    args = parser.parse_args()

    if not Path(args.csv).exists():
        print(f"✗ CSV not found: {args.csv}")
        sys.exit(1)

    rows = parse_rows(args.csv)
    if not rows:
        print("✗ No valid rows in CSV")
        sys.exit(1)

    failures = asyncio.run(provision(rows, args.out, args.login_url))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
