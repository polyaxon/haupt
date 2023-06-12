from typing import Optional

from polyaxon.connections import CONNECTION_CONFIG
from polyaxon.env_vars.getters import get_artifacts_store_name
from polyaxon.fs.fs import get_async_fs_from_connection, get_default_fs
from polyaxon.fs.types import FSSystem


class AppFS:
    _connections = {}

    @classmethod
    async def set_fs(cls, connection: Optional[str] = None) -> FSSystem:
        fs = None
        if connection:
            name = connection
            connection = CONNECTION_CONFIG.get_connection_for(connection)
            if connection:
                fs = await get_async_fs_from_connection(connection=connection)
        else:
            fs = await get_default_fs()
            name = get_artifacts_store_name()

        cls._connections[name] = fs
        return cls._connections[name]

    @classmethod
    async def close_fs(cls, connection: Optional[str] = None):
        connection = connection or get_artifacts_store_name()
        connection = cls._connections.get(connection)
        if connection and hasattr(connection, "close_session"):
            connection.close_session(connection.loop, connection.session)

    @classmethod
    async def get_fs(cls, connection: Optional[str] = None) -> FSSystem:
        connection = connection or get_artifacts_store_name()
        connection = cls._connections.get(connection)
        if not connection:
            return await cls.set_fs()
        return connection
