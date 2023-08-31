import datetime
import os
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from typing import Optional, Type
from tools.create_quotation import get_creds, copy_sheet, update_cells, rename_and_download_as_pdf
from tools.default_tool import DefaultTool
import config

load_dotenv()
open_ai_key = os.getenv('OPENAI_API_KEY', None)
scope = os.getenv('SCOPES', None)
temp_workbook_id = os.getenv('TEMP_WORKBOOK_ID', None)
TODAY = datetime.datetime.today().strftime('%Y%m%d')


class QuotationCheckInput(BaseModel):
    """Input for QuotationCreator check."""

    client: str = Field(...,
                       description="""The client name.""")
    product_name: str = Field(...,
                       description="""The product name.""")
    unit_price: str = Field(...,
                       description="""The unit price of the product.""")
    minimum_qty: str = Field(...,
                       description="""The minimum quantity of the product.""")
    until_date: str = Field(...,
                       description="""This quotation is valid until this date.""")



class QuotationCreator(DefaultTool):
    name = "create_quotation"
    description = """
            This tool aims to create quotation from google sheet template.
            For this tool, you must provide the 5 following arguments: 
            ['client', 'product_name', 'unit_price', 'minimum_qty', 'until_date'].
            The output will be a quotation pdf file. 
            """

    def _run(self,client, product_name, unit_price, minimum_qty, until_date):
        data = {
            'G8': until_date,
            'D12': client,
            'D20': product_name,
            'E20': unit_price,
            'F20': minimum_qty,
        }

        creds = get_creds()
        target_workbook_id = copy_sheet(creds, temp_workbook_id)
        update_cells(creds, target_workbook_id, data)
        config.OUTPUT_PATH = rename_and_download_as_pdf(target_workbook_id, creds, f'Quotation_{TODAY}')

        return config.OUTPUT_PATH

    args_schema: Optional[Type[BaseModel]] = QuotationCheckInput
