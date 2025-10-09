from app.core.conf import DbInit, ssl_context
from sqlalchemy.ext.asyncio import ( 
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base
from typing import Any, Awaitable, Callable
from app.core.logger import setup_logger

logger = setup_logger("database")

class DB:
    def __init__(self):
        self._dburl:str = DbInit
        self._base:Any = declarative_base()
        self.engine = create_async_engine(
            self._dburl, connect_args={"ssl":ssl_context}, echo=True
        )

    @property
    def get_base(self):
        return self._base
    
    def asyncSessionLocal(self):
        return async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession,
        )
    
    async def get_db(self):
        try:
            SessionFactory = self.asyncSessionLocal()
            async with SessionFactory() as Session:
                try:
                    yield Session
                finally:
                    await Session.close()
        except Exception as e:
            logger.error(f"Error | func=get_db | error={str(e)}")
    
    
    async def process_db_sockets(
        self, instance_class:Any,
        method_name:str,
        *args, **kwargs
    ):
        try:
            async for db in self.get_db():
                instance = instance_class(db)
                method: Callable[..., Awaitable] = getattr(instance, method_name)
                return await method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error | func=process_db_sockets | error={str(e)}")


DbInstance = DB()

