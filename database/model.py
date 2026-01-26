import datetime
from typing import Literal

from sqlalchemy import BigInteger, VARCHAR, ForeignKey, DateTime, Boolean, Column, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UsersTable(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(VARCHAR)
    name: Mapped[str] = mapped_column(VARCHAR)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    restores: Mapped[int] = mapped_column(Integer, default=10)
    revives: Mapped[int] = mapped_column(Integer, default=10)

    referral: Mapped[int] = mapped_column(BigInteger, default=None, nullable=True)
    refs: Mapped[int] = mapped_column(Integer, default=0)
    revives_earn: Mapped[int] = mapped_column(Integer, default=0)

    join: Mapped[str] = mapped_column(VARCHAR, default=None, nullable=True)

    restores_count: Mapped[int] = mapped_column(Integer, default=0)
    revives_count: Mapped[int] = mapped_column(Integer, default=0)

    active: Mapped[int] = mapped_column(Integer, default=1)
    activity: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())
    entry: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())


class DeeplinksTable(Base):
    __tablename__ = 'deeplinks'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(VARCHAR)
    link: Mapped[str] = mapped_column(VARCHAR)

    entry: Mapped[int] = mapped_column(BigInteger, default=0)

    earned: Mapped[int] = mapped_column(Integer, default=0)
    today: Mapped[int] = mapped_column(Integer, default=0)
    week: Mapped[int] = mapped_column(Integer, default=0)

    create: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())


class RatesTable(Base):
    __tablename__ = 'rates'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    rate: Mapped[Literal['restore', 'revive']] = mapped_column(VARCHAR, nullable=False)


class AdminsTable(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR)


class OneTimeLinksIdsTable(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    link: Mapped[str] = mapped_column(VARCHAR)


class StaticTable(Base):
    __tablename__ = 'static'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    total: Mapped[int] = mapped_column(Integer, default=0)
    today: Mapped[int] = mapped_column(Integer, default=0)
    week: Mapped[int] = mapped_column(Integer, default=0)
    month: Mapped[int] = mapped_column(Integer, default=0)

