from __future__ import annotations

import shutil

from sqlalchemy import text
from sqlmodel import SQLModel, Session

from app.core.config import get_settings
from app.core.db import engine
from app.core.security import hash_password
from app.models import User
from trustledger_domain import AccountWorkspaceRole, SystemRole


DEFAULT_PASSWORDS = {
    "vasilis.markopoulos@accounts.trustledger.app": "VasilisTenantAdmin123!",
    "lila.tsoutsoura@accounts.trustledger.app": "LilaLandlord123!",
    "theodore.tsoutsouras@accounts.trustledger.app": "TheodoreAgent123!",
    "froso.evangeliadou@accounts.trustledger.app": "FrosoTenantLandlord123!",
}


USER_SEED = (
    {
        "email": "vasilis.markopoulos@accounts.trustledger.app",
        "full_name": "vasilis markopoulos",
        "system_role": SystemRole.ADMIN,
        "workspace_roles": (AccountWorkspaceRole.TENANT, AccountWorkspaceRole.INTERNAL),
    },
    {
        "email": "lila.tsoutsoura@accounts.trustledger.app",
        "full_name": "lila tsoutsoura",
        "system_role": SystemRole.USER,
        "workspace_roles": (AccountWorkspaceRole.LANDLORD,),
    },
    {
        "email": "theodore.tsoutsouras@accounts.trustledger.app",
        "full_name": "theodore tsoutsouras",
        "system_role": SystemRole.USER,
        "workspace_roles": (AccountWorkspaceRole.AGENCY,),
    },
    {
        "email": "froso.evangeliadou@accounts.trustledger.app",
        "full_name": "froso evangeliadou",
        "system_role": SystemRole.USER,
        "workspace_roles": (AccountWorkspaceRole.TENANT, AccountWorkspaceRole.LANDLORD),
    },
)


def wipe_model_tables(session: Session) -> None:
    session.exec(text("PRAGMA foreign_keys=OFF"))
    for table in reversed(SQLModel.metadata.sorted_tables):
        if table.name == "alembic_version":
            continue
        session.exec(text(f'DELETE FROM "{table.name}"'))
    session.exec(text("PRAGMA foreign_keys=ON"))


def wipe_local_artifacts() -> None:
    settings = get_settings()
    artifact_root = settings.artifact_storage_root
    if settings.artifact_storage_backend == "local_private" and artifact_root:
        shutil.rmtree(artifact_root, ignore_errors=True)


def main() -> None:
    wipe_local_artifacts()
    with Session(engine) as session:
        wipe_model_tables(session)
        for user_data in USER_SEED:
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                password_hash=hash_password(DEFAULT_PASSWORDS[user_data["email"]]),
                system_role=user_data["system_role"],
                is_active=True,
                email_verified=True,
            )
            user.set_workspace_roles(user_data["workspace_roles"])
            session.add(user)
        session.commit()

    print("Trust Ledger local data wiped.")
    print("Created users only:")
    for user_data in USER_SEED:
        print(
            f"- {user_data['full_name']}: {user_data['email']} / "
            f"{DEFAULT_PASSWORDS[user_data['email']]}"
        )


if __name__ == "__main__":
    main()
