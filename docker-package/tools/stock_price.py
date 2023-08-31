from typing import Optional, Type
from pydantic import BaseModel, Field
from tools.yahoo_finance import get_stock_price
from tools.default_tool import DefaultTool

class StockPriceCheckInput(BaseModel):
    """Input for Stock price check."""

    stockticker: str = Field(...,
                             description="Ticker symbol for stock or index")


class StockPriceTool(DefaultTool):
    name = "get_stock_ticker_price"
    description = "Useful for when you need to find out the price of stock. You should input the stock ticker used on the yfinance API"

    def _run(self, stockticker: str):
        # print("i'm running")
        price_response = get_stock_price(stockticker)

        return price_response

    args_schema: Optional[Type[BaseModel]] = StockPriceCheckInput
