#!/usr/bin/env python3
"""Promote a user to active admin by email (bootstrap/recovery helper).

Usage:
    PYTHONPATH=. uv run python scripts/promote_admin.py --email you@example.com
"""

import argparse
import asyncio

from sqlalchemy import func, select, update

from src.models.user import User, UserRole, UserStatus


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a user to admin")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    async def run() -> None:
        from src.database import async_session_factory

        async with async_session_factory() as session:
            result = await session.execute(
                update(User)
                .where(func.lower(User.email) == args.email.lower())
                .values(role=UserRole.ADMIN, status=UserStatus.ACTIVE)
            )
            await session.commit()
            if result.rowcount == 0:
                exists = await session.execute(
                    select(User.id).where(func.lower(User.email) == args.email.lower())
                )
                if exists.first() is None:
                    print(f"No user found with email {args.email}. They must sign up first.")
                return
            print(f"Promoted {args.email} to active admin.")

    asyncio.run(run())


if __name__ == "__main__":
    main()
