from collections.abc import Mapping
from typing import List, Optional

from django.conf import settings


def normalize_tags(tags) -> Optional[List[str]]:
    """
    Normalize tags from SQLite dict or PostgreSQL list format to list.

    SQLite stores tags as {"tag1": "", "tag2": ""} for indexing.
    PostgreSQL stores tags as ["tag1", "tag2"].

    Args:
        tags: Tags in either dict or list format

    Returns:
        List of tag strings
    """
    if tags is None:
        return tags
    if isinstance(tags, Mapping):
        return list(tags.keys())
    return list(tags) if tags else []


def denormalize_tags(tags: Optional[List[str]]):
    """
    Convert tags to storage format based on database engine.

    SQLite requires dict format for JSON indexing.
    PostgreSQL uses native list/array format.

    Args:
        tags: List of tag strings

    Returns:
        Dict for SQLite, list for PostgreSQL
    """
    if tags is None:
        return tags
    if settings.DB_ENGINE_NAME == "sqlite":
        return {t: "" for t in tags}
    return tags
