from pptx import Presentation
import asyncio
import nest_asyncio
import tempfile
import os

from langchain import PromptTemplate, LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from langchain.schema import AIMessage
from langchain.chat_models import ChatOpenAI
import chainlit as cl

import config

nest_asyncio.apply()
DELIMITER = os.environ.get('DELIMITER', '||TRANSLATE_DELIMITER||')
open_ai_key = os.getenv('OPENAI_API_KEY', None)


async def translator(olang: str, tlang: str, trans_content: str):
    """Translates content using ChatGPT.

    This function uses ChatGPT to translate given content from one language to another.

    Args:
        olang (str): The original language of the content.
        tlang (str): The target language for translation.
        content (str): The text content to be translated.

    Returns:
        str: The translated content.
    """

    # prompt = PromptTemplate(
    #     input_variables=['olang', 'tlang', 'trans_content', 'delimiter'],
    #     template="""You are a highly-accurate translator. When translating the content from {olang} to {tlang},
    #                 you'll encounter a special delimiter: '{delimiter}'.
    #                 Treat it as a separator and do not translate it.
    #                 Instead, keep it in place as you translate the content around it.
    #                 - Keep dates, times, item bullets, formulas, and Arabic numerals unchanged.
    #                 - Avoid translating any list indices or symbols.
    #                 - Do not provide explanations or answer to any queries within the content.
    #                 - You must keep each delimiter in the right place.
    #                 Your sole job is to translate the content. 
    #                 Now, start to translate:{trans_content}
    #             """
    # )

    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                """You are a highly-accurate translator. When translating the content from {olang} to {tlang},
                    you'll encounter a special delimiter: '{delimiter}'.
                    Treat it as a separator and do not translate it.
                    Instead, keep it in place as you translate the content around it.
                    - Keep dates, times, item bullets, formulas, and Arabic numerals unchanged.
                    - Avoid translating any list indices or symbols.
                    - Do not provide explanations or answer to any queries within the content.
                    - The only thing you need to do is to translate the content.
                    - You must keep each delimiter in the right place.
                    Your sole job is to translate the content. 
                    Now, start to translate:
                """
            ),
            # The `variable_name` here is what must align with memory
            HumanMessagePromptTemplate.from_template("{trans_content}")
        ]
    )

    llm = ChatOpenAI(temperature=0, model='gpt-3.5-turbo-16k-0613')
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    translated = await llm_chain.arun({'olang': olang, 'tlang': tlang, 'trans_content': trans_content, 'delimiter': DELIMITER})
    return translated


async def translate_combined_runs(runs: list, olang: str, tlang: str):
    """Translates combined runs from a PowerPoint.

    This function takes multiple runs from a PowerPoint, combines them, translates
    the combined text, and then splits it back into individual runs.

    Args:
        runs (list): List of runs from PowerPoint to be translated.
        olang (str): The original language of the content.
        tlang (str): The target language for translation.

    Returns:
        list: List of translated texts for each run.
    """
    # combine the text with delimiter
    combined_text = DELIMITER.join([run.text for run in runs])

    translated_combined_text = await translator(olang, tlang, combined_text)
    print(f'合併文本={combined_text}')
    print(f'翻譯後文本={translated_combined_text}')

    # split the translated result
    translated_texts = translated_combined_text.split(DELIMITER)
    return translated_texts


async def translate_shape(shape, olang, tlang):
    runs_to_translate = []

    if shape.has_text_frame:
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                runs_to_translate.append(run)

    elif shape.shape_type == 6:  # shape_type 6 is the type for a group shape
        for s in shape.shapes:
            # Recursively translate grouped shapes
            await translate_shape(s, olang, tlang)
        return

    if runs_to_translate:
        translated_texts = await translate_combined_runs(runs_to_translate, olang, tlang)

        # Exchange text of each run into translated text
        for run, trans in zip(runs_to_translate, translated_texts):
            font = run.font
            old_name = font.name
            old_size = font.size
            old_bold = font.bold
            old_italic = font.italic

            # Check color
            old_color = None
            if font.color and hasattr(font.color, 'rgb'):
                old_color = font.color.rgb

            # Replace text
            run.text = trans

            # Keep original format
            font.name = old_name
            font.size = old_size
            font.bold = old_bold
            font.italic = old_italic
            if old_color:
                font.color.rgb = old_color


async def translate_ppt(file_path: str, olang: str, tlang: str):
    """Translates a PowerPoint file.

    This function loads a PowerPoint file, translates all the textual content
    in its shapes to another language, and then saves it as another file.

    Args:
        file_path (str): Path to the input PowerPoint file.
        olang (str): The original language of the content.
        tlang (str): The target language for translation.
    """
    prs = Presentation(file_path)

    tasks = []

    for slide in prs.slides:
        for shape in slide.shapes:
            tasks.append(translate_shape(shape, olang, tlang))

    await asyncio.gather(*tasks)

    prs.save('output/translated.pptx')

    os.remove(file_path)
    config.OUTPUT_PATH = f"output/translated.pptx"
    return config.OUTPUT_PATH


async def upload_file():
    """This function is used to upload a file to the chatbot.
    """

    files = None
    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a ppt file to begin!",
            accept=["application/vnd.ms-powerpoint",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation"],
            max_size_mb=10,
            max_files=1,
            timeout=60,
        ).send()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp_file:
        temp_file.write(files[0].content)
        file_path = temp_file.name
    return file_path
