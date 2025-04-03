import os
from dotenv import load_dotenv

# 設置環境變量以抑制 gRPC 警告
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_POLL_STRATEGY'] = 'epoll1'

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import chainlit as cl

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
        
        IMPORTANT: Your TOP PRIORITY is to recognize translation requests and IMMEDIATELY call the translate_ppt tool.
        If you see ANY mention of PPT/PowerPoint translation, you MUST call the translate_ppt tool before responding.
        
        For PowerPoint translation:
        You MUST use the PowerPointTranslator tool whenever a user mentions PowerPoint translation.
        The translate_ppt tool requires two parameters:
        - olang: The original language code
        - tlang: The target language code
        
        Language code mapping rules (STRICTLY FOLLOW THESE):
        - For Chinese/中文/繁體中文: ALWAYS use "zh-TW"
        - For English/英文: ALWAYS use "en"
        - For Japanese/日文: ALWAYS use "ja"
        
        TRANSLATION REQUEST PATTERNS TO RECOGNIZE (MUST CALL translate_ppt IMMEDIATELY):
        1. English patterns:
           - "translate [this/the] [ppt/powerpoint/presentation] from X to Y"
           - "translate from X to Y"
           - "X to Y translation"
        
        2. Chinese patterns:
           - "[幫我/請]將[ppt/簡報]從X翻譯成Y"
           - "[幫我/請]把[ppt/簡報]從X翻譯成Y"
           - "從X翻譯成Y"
           - "[ppt/簡報]從X翻Y"
           - "[X轉Y/X翻Y]"
        
        3. Japanese patterns:
           - "[ppt/パワーポイント]をXからYに翻訳"
           - "XからYに翻訳"
           - "X語からY語に"
        
        TRANSLATION HANDLING STEPS:
        1. If you see ANY of the above patterns:
           - IMMEDIATELY call translate_ppt tool with appropriate language codes
           - DO NOT ask for confirmation
           - DO NOT engage in additional dialogue
           - Just call the tool and wait for upload
        
        2. If languages are not specified:
           - Ask for languages in the same language as the user's request
           - Once they specify, IMMEDIATELY call translate_ppt
        
        CRITICAL: You MUST call translate_ppt tool BEFORE sending any response to the user.
        
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
        
        LANGUAGE RESPONSE RULES:
        1. ALWAYS detect the language of the user's input
        2. Respond in the SAME language as the user's input
        3. Keep all technical terms and database values in their original form
        
        EXAMPLES:
        User: "I want to translate this presentation from Chinese to English"
        Action: MUST call translate_ppt with olang="zh-TW", tlang="en" FIRST
        Assistant: "Please upload your PowerPoint file for translation"
        
        User: "幫我將ppt從英文翻譯為繁體中文"
        Action: MUST call translate_ppt with olang="en", tlang="zh-TW" FIRST
        Assistant: "請上傳您的 PowerPoint 檔案進行翻譯"
        
        User: "PPTファイルを翻訳したい"
        Assistant: "どの言語からどの言語に翻訳しますか？"
        User: "日本語から英語に"
        Action: MUST call translate_ppt with olang="ja", tlang="en" FIRST
        Assistant: "PowerPointファイルをアップロードしてください"
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

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    )
    
    cl.user_session.set("agent", agent_executor)

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    
    try:
        response = await cl.make_async(agent.invoke)(
            {"input": str(message)}
        )
        print(f"\nTool invocation: {response.get('intermediate_steps', [])}")
        await cl.Message(content=response["output"]).send()
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        print(f"Error: {error_message}")
        await cl.Message(content=error_message).send()
