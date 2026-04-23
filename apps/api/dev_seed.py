from __future__ import annotations

from sqlmodel import Session

from app.core.db import engine
from app.devtools import seed_demo_environment


def main() -> None:
    with Session(engine) as session:
        summary = seed_demo_environment(session=session)

    print("Trust Ledger demo seed complete.")
    print("")
    print("Demo accounts:")
    for account in summary.accounts:
        print(f"- {account.label}: {account.email} / {account.password}")
    print("")
    print(f"Seeded tenant share token: {summary.share_token}")
    print(f"Seeded tenant access code: {summary.access_code}")
    print("")
    print(
        "Seeded trust profile summary: "
        f"tenant_score={summary.tenant_score}, "
        f"landlord_score={summary.landlord_score}, "
        f"verification_strength={summary.verification_strength}"
    )


if __name__ == "__main__":
    main()
