import asyncio
from logging.config import fileConfig


from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import create_engine
from app.core.conf import DbInit, ssl_context
from app.core.database import DbInstance
from app.models import message_model, auth_model

config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = DbInstance.get_base.metadata


def get_url() -> str:
    return DbInit


connectable = create_engine(
    get_url(),
    connect_args={"sslmode": "require", "sslrootcert": ssl_context}
)


def run_migrations_offline():
    """Run migrations in offline mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in online async mode."""
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        # run_sync runs the sync function (do_migrations) in async context
        await connection.run_sync(do_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())