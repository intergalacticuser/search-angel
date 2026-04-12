"""Create OpenSearch indexes with full mapping."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search_angel.config import get_settings
from search_angel.search.client import OpenSearchClient
from search_angel.search.index_manager import IndexManager


async def main() -> None:
    settings = get_settings()
    client = OpenSearchClient(settings)
    manager = IndexManager(client, settings)

    print(f"Creating index '{settings.os_index_name}'...")
    created = await manager.create_index()

    if created:
        print("Index created successfully!")
        mapping = await manager.get_mapping()
        print(f"Mapping: {list(mapping.keys())}")
    else:
        print("Index already exists.")
        count = await manager.get_doc_count()
        print(f"Current document count: {count}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
