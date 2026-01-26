import datetime

from sqlalchemy import select, insert, update, column, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.model import (UsersTable, DeeplinksTable, OneTimeLinksIdsTable, AdminsTable, StaticTable, RatesTable)


async def configurate_tables(sessions: async_sessionmaker):
    async with sessions() as session:
        if not await session.scalar(select(StaticTable)):
            await session.execute(insert(StaticTable))
        await session.commit()


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session

    async def check_user(self, user_id: int) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return True if result else False

    async def add_user(self, user_id: int, username: str, name: str, referral: int | None = None, link: str | None = None):
        if await self.check_user(user_id):
            return
        async with self._sessions() as session:
            await session.execute(insert(UsersTable).values(
                user_id=user_id,
                username=username,
                name=name,
                referral=referral,
                join=link
            ))
            await session.commit()

    async def add_refs(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                refs=UsersTable.refs + 1
            ))
            await session.commit()

    async def add_deeplink(self, link: str, name: str):
        async with self._sessions() as session:
            await session.execute(insert(DeeplinksTable).values(
                link=link,
                name=name
            ))
            await session.commit()

    async def add_entry(self, link: str):
        async with self._sessions() as session:
            await session.execute(update(DeeplinksTable).where(DeeplinksTable.link == link).values(
                entry=DeeplinksTable.entry+1
            ))
            await session.commit()

    async def add_link(self, link: str):
        async with self._sessions() as session:
            await session.execute(insert(OneTimeLinksIdsTable).values(
                link=link
            ))
            await session.commit()

    async def add_admin(self, user_id: int, name: str):
        async with self._sessions() as session:
            await session.execute(insert(AdminsTable).values(
                user_id=user_id,
                name=name
            ))
            await session.commit()

    async def add_rate(self, amount: int, cost: int, text: str | None, rate: str):
        async with self._sessions() as session:
            await session.execute(insert(RatesTable).values(
                amount=amount,
                cost=cost,
                text=text,
                rate=rate
            ))
            await session.commit()

    async def add_income(self, income: int):
        async with self._sessions() as session:
            await session.execute(update(StaticTable).values(
                total=StaticTable.total + income,
                today=StaticTable.today + income,
                week=StaticTable.week + income,
                month=StaticTable.month + income
            ))
            await session.commit()

    async def get_static(self):
        async with self._sessions() as session:
            result = await session.scalar(select(StaticTable))
        return result

    async def get_users(self):
        async with self._sessions() as session:
            result = await session.scalars(select(UsersTable))
        return result.fetchall()

    async def get_user(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return result

    async def get_user_by_username(self, username: str):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.username == username))
        return result

    async def get_links(self):
        async with self._sessions() as session:
            result = await session.scalars(select(OneTimeLinksIdsTable))
        return result.fetchall()

    async def get_admins(self):
        async with self._sessions() as session:
            result = await session.scalars(select(AdminsTable))
        return result.fetchall()

    async def get_rates(self):
        async with self._sessions() as session:
            result = await session.scalars(select(RatesTable))
        return result.fetchall()

    async def get_rate(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(RatesTable).where(RatesTable.id == id))
        return result

    async def get_deeplinks(self):
        async with self._sessions() as session:
            result = await session.scalars(select(DeeplinksTable))
        return result.fetchall()

    async def get_deeplink(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(DeeplinksTable).where(DeeplinksTable.id == id))
        return result

    async def update_deeplink_earn(self, link: str, earn: int):
        async with self._sessions() as session:
            await session.execute(update(DeeplinksTable).where(DeeplinksTable.link == link).values(
                earned=DeeplinksTable.earned + earn,
                today=DeeplinksTable.today + earn,
                week=DeeplinksTable.week + earn
            ))
            await session.commit()

    async def set_deeplink_value(self, deeplink_id: int, **kwargs):
        async with self._sessions() as session:
            await session.execute(update(DeeplinksTable).where(DeeplinksTable.id == deeplink_id).values(
                kwargs
            ))
            await session.commit()

    async def set_activity(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                activity=datetime.datetime.today()
            ))
            await session.commit()

    async def set_active(self, user_id: int, active: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                active=active
            ))
            await session.commit()

    async def set_static_value(self, **kwargs):
        async with self._sessions() as session:
            await session.execute(update(StaticTable).values(
                kwargs
            ))
            await session.commit()

    async def increment_user_value(self, user_id: int, column: str, value: any):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                {
                    getattr(UsersTable, column): getattr(UsersTable, column) + value
                }
            ))
            await session.commit()

    async def del_deeplink(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(DeeplinksTable).where(DeeplinksTable.id == id))
            await session.commit()

    async def del_link(self, link_id: str):
        async with self._sessions() as session:
            await session.execute(delete(OneTimeLinksIdsTable).where(OneTimeLinksIdsTable.link == link_id))
            await session.commit()

    async def del_admin(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(AdminsTable).where(AdminsTable.user_id == user_id))
            await session.commit()

    async def del_rate(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(RatesTable).where(RatesTable.id == id))
            await session.commit()
