"""Base adapter interface for HFI content ingestion."""

from abc import ABC, abstractmethod

from langchain_core.documents import Document


class BaseAdapter(ABC):
    @abstractmethod
    async def fetch(self, source) -> list[Document]:
        """Fetch documents from the source. Returns LangChain Documents."""
        ...
