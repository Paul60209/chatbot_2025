import os

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.utilities import SQLDatabase
from langchain.llms import OpenAI
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate

from tools.default_tool import DefaultTool


class SQLQueryCheckInput(BaseModel):
    """Input for execute_sql_query check."""

    query: str = Field(...,
                       description="SQL query to select data or statistic result from database")


class SQLQueryTool(DefaultTool):
    name = "execute_sql_query"
    # description = """
    #         Input to this tool is a detailed and correct SQL query, output is a result from the database.
    #         If the query is not correct, an error message will be returned.
    #         If an error is returned, rewrite the query, check the query, and try again.
    #         """
    description = """
            This tool is useful for when you need to find out the result of a SQL query.
            """

    def _run(self, query: str):
        db_url = os.getenv('CLEARDB_DATABASE_URL', None).split('?')[0]
        open_ai_key = os.getenv('OPENAI_API_KEY', None)

        # TEMPLATE = """Given an input question, first create a syntactically correct 
        #             'select' query to run, then look at the results of the query and return the answer.
        #             Use the following format:

        #             Question: "Question here"
        #             SQLQuery: "SQL Query to run"
        #             SQLResult: "Result of the SQLQuery"
        #             Answer: "Final answer here"

        #             Only use the following tables:

        #             sales.

        #             Some examples of SQL queries that corrsespond to questions are:

        #             {
        #                 {'ID':['ID07351', 'ID07352', 'ID07353']},
        #                 {'Date':['2023/1/1', '2023/1/4', '2023/1/7']},
        #                 {'Region':['関東', '関西', '関東']},
        #                 {'City':['東京', '京都', '千葉']},
        #                 {'Category':['野菜', '野菜', '果物']},
        #                 {'Product':['キャベツ', '玉ねぎ', 'リンゴ']},
        #                 {'Quantity':[33, 87, 58]},
        #                 {'Unit_Price':[244, 481, 258]},
        #                 {'Total_Price':[8052, 41847, 14964]},
        #             }

        #             Question: {input}
        #             """

        # CUSTOM_PROMPT = PromptTemplate(
        #     input_variables=["input"], template=TEMPLATE
        # )
        llm = OpenAI(temperature=0, openai_api_key=open_ai_key,
                     model_name='gpt-3.5-turbo')

        db = SQLDatabase.from_uri(db_url)
        db_chain = SQLDatabaseChain.from_llm(
            llm, db, verbose=True, )
        result = db_chain.run(query)
        return result

    args_schema: Optional[Type[BaseModel]] = SQLQueryCheckInput
