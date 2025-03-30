import os
from dotenv import load_dotenv

# 設置環境變量以抑制 gRPC 警告
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_POLL_STRATEGY'] = 'epoll1'

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import chainlit as cl

import config
from tools.sql_query import SQLQueryTool
from tools.translator import PowerPointTranslator

load_dotenv()
open_ai_key = os.getenv('OPENAI_API_KEY', None)
db_url = os.getenv('CLEARDB_DATABASE_URL', None)

@cl.on_chat_start
async def start():
    # 設置 callbacks
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    # Model
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini-2024-07-18",
        streaming=True,
        callback_manager=callback_manager
    )

    # Tools
    tools = [SQLQueryTool(), PowerPointTranslator()]

    # System Message
    system_message = """You are a nice chatbot who can help users query the sales database and translate PowerPoint files.
        
        For database queries:
        You can execute SQL queries to get information from the database.
        The database has a 'sales' table with the following columns:
        - ID (VARCHAR)
        - Date (DATE)
        - Region (VARCHAR) - Values: 関東, 関西
        - City (VARCHAR) - Values: 東京, 横浜, 埼玉, 千葉, 京都, 大阪, 神戸
        - Category (VARCHAR) - Values: 野菜, 果物
        - Product (VARCHAR) - Various products like キャベツ, 玉ねぎ, トマト, リンゴ, みかん, バナナ
        - Quantity (INT)
        - Unit_Price (DECIMAL)
        - Total_Price (DECIMAL)
        
        For PowerPoint translation:
        IMPORTANT: You MUST ALWAYS use the translate_ppt tool for ANY request related to PowerPoint or PPT translation.
        DO NOT ask questions or make suggestions - IMMEDIATELY call the tool with appropriate parameters.
        
        Language code mapping (STRICT RULES - NO EXCEPTIONS):
        - Chinese (中文/中國語/華語): ALWAYS use "zh-TW"
        - English (英文/英語): ALWAYS use "en"
        - Japanese (日文/日語): ALWAYS use "ja"
        
        TRANSLATION REQUEST HANDLING:
        1. When user mentions translation in ANY way (including words like "翻譯", "translate", "轉換語言"):
           - IMMEDIATELY identify source and target languages
           - Call translate_ppt with correct language codes
           - Example: translate_ppt(olang="zh-TW", tlang="en")
           - Then say "好的，請上傳您要翻譯的 PowerPoint 文件"
        
        2. If languages are not specified:
           - Ask "請問您要將 PowerPoint 從哪種語言翻譯成哪種語言？"
           - Once user specifies languages, IMMEDIATELY call translate_ppt
        
        CRITICAL RULES:
        - NEVER skip calling the translate_ppt tool for translation requests
        - NEVER wait for file upload before calling the tool
        - NEVER ask for language confirmation if languages are already specified
        - ALWAYS call translate_ppt BEFORE asking for file upload
        
        EXAMPLES:
        User: "幫我翻譯這個PPT"
        Assistant: "請問您要將 PowerPoint 從哪種語言翻譯成哪種語言？"
        
        User: "從中文翻譯成英文"
        Assistant: "好的，請上傳您要翻譯的 PowerPoint 文件"
        Action: MUST call translate_ppt(olang="zh-TW", tlang="en")
        
        User: "我要把簡報從日文轉成中文"
        Assistant: "好的，請上傳您要翻譯的 PowerPoint 文件"
        Action: MUST call translate_ppt(olang="ja", tlang="zh-TW")
        
        Always communicate in Traditional Chinese (繁體中文).
        """

    # Memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Agent
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    )
    
    cl.user_session.set("agent", agent_executor)

@cl.on_message
async def main(message):
    agent = cl.user_session.get("agent")
    
    try:
        print(f"\n用戶輸入: {message}")
        print(f"可用工具: {[tool.name for tool in agent.tools]}")
        response = await cl.make_async(agent.invoke)(
            {"input": message.content}
        )
        print(f"\n工具調用: {response.get('intermediate_steps', [])}")
        print(f"LLM回覆: {response['output']}\n")
        await cl.Message(content=response["output"]).send()
    except Exception as e:
        error_message = f"發生錯誤：{str(e)}"
        print(f"錯誤: {error_message}")
        await cl.Message(content=error_message).send()
