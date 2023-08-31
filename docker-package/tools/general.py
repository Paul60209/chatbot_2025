from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field
from tools.default_tool import DefaultTool

class GeneralCheckInput(BaseModel):
    """If there is no tool for your task, use this tool to get a general answer"""

    query: str = Field(...,
                             description="If there is no tool for your task, use this tool to get a general answer")

class GeneralTool(DefaultTool):
    name = "answer_general_question"
    description = """
            If there is no tool for your task, use this tool to get a general answer
            """
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    prompt = PromptTemplate(
            input_variables=["query"],
            template="{query}"
        )

    llm_chain = LLMChain(llm=llm, prompt=prompt)

    def _run(self, query: str):
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

        prompt = PromptTemplate(
                input_variables=["query"],
                template="{query}"
            )

        llm_chain = LLMChain(llm=llm, prompt=prompt)

        
        result = llm_chain.run(query)
        return result




