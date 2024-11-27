import json
import logging

from typing import AsyncGenerator

from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import sessionmaker

from contextlib import asynccontextmanager

from sqlalchemy import inspect, text, ARRAY, JSON, Boolean, Integer, Float, String, Date, DateTime, Time

engine = create_async_engine(
    'postgresql+asyncpg://postgres:postgres@postgres_db:5432/communication',
    echo=False,
    future=True,
    pool_size=75,
    max_overflow=125,
    pool_recycle=600,
    pool_pre_ping=True,
    poolclass=AsyncAdaptedQueuePool
)

Base = declarative_base()

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def format_default_value(column):
    default = column.default.arg if column.default is not None else None

    if default is not None:
        if isinstance(column.type, ARRAY):
            default = f"ARRAY{default}" if isinstance(default, list) else f"ARRAY[{default}]"
        elif isinstance(column.type, JSON):
            default = f"'{json.dumps(default)}'::json"
        elif isinstance(column.type, Boolean):
            default = 'TRUE' if default else 'FALSE'
        elif isinstance(column.type, (Integer, Float)):
            default = str(default)
        elif isinstance(column.type, (String, Date, DateTime, Time)):
            default = f"'{default}'"
        else:
            default = f"'{default}'"

    return default


async def init_models() -> None:
    async with engine.begin() as conn:
        try:
            try:
                await conn.run_sync(Base.metadata.create_all)
            except Exception as e:
                logging.error(f"Error while initializing models: {e}")

            inspector = await conn.run_sync(inspect)

            try:
                for table_name, model in Base.metadata.tables.items():
                    table_exists = await conn.run_sync(lambda sync_conn: inspector.has_table(table_name))

                    if table_exists:
                        existing_columns = await conn.run_sync(lambda sync_conn: inspector.get_columns(table_name))

                        existing_column_names = [column['name'] for column in existing_columns]

                        for column in model.columns:
                            if column.name not in existing_column_names:
                                column_name = column.name
                                column_type = column.type.compile(dialect=conn.dialect)

                                nullable = "NULL" if column.nullable else "NOT NULL"

                                default_value = format_default_value(column)

                                if default_value:
                                    column_sql = f"{column_name} {column_type} {nullable} DEFAULT {default_value}"
                                else:
                                    column_sql = f"{column_name} {column_type} {nullable}"

                                await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))
            except Exception as e:
                logging.error(f"Error while initializing models: {e}")
        except Exception as e:
            logging.error(f"Error while initializing models: {e}")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
