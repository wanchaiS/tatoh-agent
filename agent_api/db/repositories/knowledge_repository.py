from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_key(self, key: str) -> KnowledgeDocument | None:
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.key == key)
        )
        return result.scalars().first()
