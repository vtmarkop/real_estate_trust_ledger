from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def create_engine_from_url(database_url: str, *, echo: bool = False):
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {"echo": echo}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            engine_kwargs["poolclass"] = StaticPool
    else:
        engine_kwargs["pool_pre_ping"] = True

    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


settings = get_settings()
engine = create_engine_from_url(settings.database_url, echo=settings.database_echo)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
