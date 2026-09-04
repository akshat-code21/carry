#!/usr/bin/env python3
"""Create an invite code from the CLI (invite helper).

Usage:
    PYTHONPATH=. uv run python scripts/create_invite.py \
        [--email someone@example.com] [--max-uses 1] [--expires-in-days 30]

Then share the printed code (or signup URL) with the invited person.
Note: invites never grant admin - promote admins via Clerk public metadata.
"""

import argparse
import asyncio


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an invite code")
    parser.add_argument("--email", default=None, help="Restrict redemption to this email")
    parser.add_argument("--max-uses", type=int, default=1, help="Number of redemptions allowed")
    parser.add_argument("--expires-in-days", type=int, default=None)
    args = parser.parse_args()

    async def run() -> None:
        from src.auth.service import create_invite
        from src.database import async_session_factory

        async with async_session_factory() as session:
            invite = await create_invite(
                session,
                created_by_user_id=None,
                invited_email=args.email,
                max_uses=max(1, args.max_uses),
                expires_in_days=args.expires_in_days,
            )
            await session.commit()
            print("Invite created:")
            print(f"  code: {invite.code}")
            if args.email:
                print(f"  bound to email: {args.email}")
            print(f"  uses allowed: {invite.max_uses}")
            if args.expires_in_days:
                print(f"  expires in: {args.expires_in_days} days")

    asyncio.run(run())


if __name__ == "__main__":
    main()
