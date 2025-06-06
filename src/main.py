import os
from fastapi import FastAPI
from src.database.connection import db
from src.routers.api import api

async def startup():
    dsn = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/collagrcms")
    await db.connect(dsn)

async def shutdown():
    await db.close()

def main():
    api.add_event_handler("startup", startup)
    api.add_event_handler("shutdown", shutdown)

if __name__ == "__main__":
    main()
