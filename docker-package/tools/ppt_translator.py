import nest_asyncio
import os

from pydantic import BaseModel, Field
from typing import Optional, Type
from tools.translator import upload_file, translate_ppt
from tools.default_tool import DefaultTool
import config

nest_asyncio.apply()
DELIMITER = os.environ.get('DELIMITER', '||TRANSLATE_DELIMITER||')
open_ai_key = os.getenv('OPENAI_API_KEY', None)


class PowerPointCheckInput(BaseModel):
    """Input for power point translate check."""

    olang: str = Field(...,
                       description="""The original language of the content.""")
    tlang: str = Field(...,
                       description="""The target language for translation.""")


class PowerPointTranslator(DefaultTool):
    name = "translate_ppt"
    description = """
            This tool aims to translate a PowerPoint file from one language to another.
            For this tool, you must provide the 2 following arguments: ['olang', 'tlang'].
            'olang' stands for the original language 
            and 'tlang' stands for the target language,
            The output will be a translated PowerPoint file. 
            """

    def _run(self, olang: str, tlang: str):
        """Translates a PowerPoint file.

        This function loads a PowerPoint file, translates all the textual content
        in its shapes to another language, and then saves it as another file.

        Args:
            input_file (str): Path to the input PowerPoint file.
            output_file (str): Path to save the translated PowerPoint file.
            olang (str): The original language of the content.
            tlang (str): The target language for translation.
        """
        raise NotImplementedError("This tool does not support sync")

    async def _arun(self, olang: str, tlang: str):
        """Translates a PowerPoint file.

        This function loads a PowerPoint file, translates all the textual content
        in its shapes to another language, and then saves it as another file.

        Args:
            input_file (str): Path to the input PowerPoint file.
            output_file (str): Path to save the translated PowerPoint file.
            olang (str): The original language of the content.
            tlang (str): The target language for translation.
        """
        file_path = await upload_file()
        config.OUTPUT_PATH = await translate_ppt(file_path, olang, tlang)

        return config.OUTPUT_PATH

    args_schema: Optional[Type[BaseModel]] = PowerPointCheckInput
