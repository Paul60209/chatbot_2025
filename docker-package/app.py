import os
from dotenv import load_dotenv

import langchain
from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import chainlit as cl

import config
from tools.stock_price import StockPriceTool
from tools.stock_performance import StockPercentageChangeTool, StockGetBestPerformingTool
from tools.sql_query import SQLQueryTool
from tools.ppt_translator import PowerPointTranslator
from tools.quotation_tool import QuotationCreator

langchain.debug = True

load_dotenv()
channel_secret = os.getenv('ChannelSecret', None)
channel_access_token = os.getenv('ChannelAccessToken', None)
open_ai_key = os.getenv('OPENAI_API_KEY', None)
db_url = os.getenv('CLEARDB_DATABASE_URL', None)


@cl.on_chat_start
async def start():
    # Model
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    # Prompt
    template = """You are a nice chatbot who can use suitable tool to figure out user's question.

    Previous conversation:
    {chat_history}

    New user question: {question}
    Response:
    """
    prompt = PromptTemplate.from_template(template)

    # Memory
    memory = ConversationBufferMemory(memory_key="chat_history")

    # # General tool
    # llm_chain = LLMChain(llm=llm, prompt=prompt)
    # llm_tool = Tool(
    #     name='answer_general_question',
    #     func=llm_chain.run,
    #     description='If there is no tool for your task, use this tool to get a general answer'
    # )

    # Tools
    tools = [StockPriceTool(), StockPercentageChangeTool(),
             StockGetBestPerformingTool(), SQLQueryTool(),
             PowerPointTranslator(), QuotationCreator()]

    # Agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        # agent=AgentType.OPENAI_MULTI_FUNCTIONS,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        prompt=prompt,
        memory=memory,
    )
    cl.user_session.set("agent", agent)


@cl.on_message
async def main(message):
    config.OUTPUT_PATH = None
    agent = cl.user_session.get("agent")
    # cb = cl.LangchainCallbackHandler(stream_final_answer=False)
    # res = await cl.make_async(agent.run)(message, callbacks=[cb])
    res = await agent.arun(message)

    if config.OUTPUT_PATH == None:
        await cl.Message(content=res).send()
    else:
        print(f"提示: output={config.OUTPUT_PATH}")
        elements = [
            cl.File(
                name=config.OUTPUT_PATH.split("/")[-1],
                path=f"{config.OUTPUT_PATH}",
                display="inline",
            ),
        ]

        await cl.Message(
            content="This is the output file.", elements=elements
        ).send()
