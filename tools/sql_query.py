import os

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain import SQLDatabase, SQLDatabaseChain
from langchain.llms.openai import OpenAI

from tools.default_tool import DefaultTool


class SQLQueryCheckInput(BaseModel):
    """Input for Stock ticker check. for percentage check"""

    query: str = Field(...,
                       description="SQL query to select data or statistic result from database")


class SQLQueryTool(DefaultTool):
    name = "execute_sql_query"
    description = """
            Input to this tool is a detailed and correct SQL query, output is a result from the database.
            If the query is not correct, an error message will be returned.
            If an error is returned, rewrite the query, check the query, and try again.
            """

    def _run(self, query: str):
        db_url = os.getenv('CLEARDB_DATABASE_URL', None).split('?')[0]
        open_ai_key = os.getenv('OPENAI_API_KEY', None)
        llm = OpenAI(temperature=0, openai_api_key=open_ai_key,
                     model_name='gpt-3.5-turbo')

        db = SQLDatabase.from_uri(db_url)
        db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)
        result = db_chain.run(query)
        return result

    args_schema: Optional[Type[BaseModel]] = SQLQueryCheckInput
