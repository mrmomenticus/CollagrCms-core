from src.database.connection import DatabaseConnection
from src.database.queries.base import BaseQueries


class DatabaseInit(BaseQueries):
    def __call__(self):
        return self.execute_sql_file("schema.sql")
