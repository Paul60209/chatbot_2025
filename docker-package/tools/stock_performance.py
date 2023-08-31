from typing import List
from typing import Optional, Type
from pydantic import BaseModel, Field
from tools.yahoo_finance import get_price_change_percent, get_best_performing
from tools.default_tool import DefaultTool


class StockChangePercentageCheckInput(BaseModel):
    """Input for Stock ticker check. for percentage check"""

    stockticker: str = Field(...,
                             description="Ticker symbol for stock or index")
    days_ago: int = Field(..., description="Int number of days to look back")


class StockPercentageChangeTool(DefaultTool):
    name = "get_price_change_percent"
    description = "Useful for when you need to find out the percentage change in a stock's value. You should input the stock ticker used on the yfinance API and also input the number of days to check the change over"

    def _run(self, stockticker: str, days_ago: int):
        price_change_response = get_price_change_percent(stockticker, days_ago)

        return price_change_response

    args_schema: Optional[Type[BaseModel]] = StockChangePercentageCheckInput


# the best performing

class StockBestPerformingInput(BaseModel):
    """Input for Stock ticker check. for percentage check"""

    stocktickers: List[str] = Field(...,
                                    description="Ticker symbols for stocks or indices")
    days_ago: int = Field(..., description="Int number of days to look back")


class StockGetBestPerformingTool(DefaultTool):
    name = "get_best_performing"
    description = "Useful for when you need to the performance of multiple stocks over a period. You should input a list of stock tickers used on the yfinance API and also input the number of days to check the change over"

    def _run(self, stocktickers: List[str], days_ago: int):
        price_change_response = get_best_performing(stocktickers, days_ago)

        return price_change_response

    args_schema: Optional[Type[BaseModel]] = StockBestPerformingInput
