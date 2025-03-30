import os
import pymysql
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_community.llms import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

from tools.default_tool import DefaultTool


class SQLQueryCheckInput(BaseModel):
    """Input for execute_sql_query check."""

    query: str = Field(...,
                       description="SQL query to select data or statistic result from database")


class SQLQueryTool(DefaultTool):
    name = "execute_sql_query"
    description = """
            This tool is useful for when you need to find out the result of a SQL query.
            """

    def _run(self, query: str):
        db_url = os.getenv('CLEARDB_DATABASE_URL', None)
        if not db_url:
            return "Database URL not found in environment variables"

        try:
            # Parse the MySQL URL
            # Format: mysql://user:pass@host:port/dbname
            db_url = db_url.replace('mysql://', '')
            if '@' in db_url:
                auth, rest = db_url.split('@')
                user = auth.split(':')[0]
                password = auth.split(':')[1] if ':' in auth else None
            else:
                user = 'root'
                password = None
                rest = db_url

            if '/' in rest:
                host_port, dbname = rest.split('/')
            else:
                host_port = rest
                dbname = None

            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 3306

            # Connect to the database
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=dbname,
                port=port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchall()
                    return result
            finally:
                connection.close()

        except Exception as e:
            return f"Error executing query: {str(e)}"

    args_schema: Optional[Type[BaseModel]] = SQLQueryCheckInput
