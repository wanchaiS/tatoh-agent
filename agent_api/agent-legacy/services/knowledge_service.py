from db.database import AsyncSessionLocal
from db.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeService:
    """Async service for knowledge document lookups from Postgres."""

    async def get_document(self, key: str) -> dict | None:
        async with AsyncSessionLocal() as db:
            doc = await KnowledgeRepository(db).get_by_key(key)
            if not doc:
                return None
            return {
                "details": doc.content,
                "image_urls": doc.image_urls,
            }


knowledge_service = KnowledgeService()
