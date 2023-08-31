from typing import Any, Coroutine
from langchain.tools import BaseTool

class DefaultTool(BaseTool):
    async def _arun(self, *args: Any, **kwargs: Any) -> Coroutine[Any, Any, Any]:
        result = self._run(*args, **kwargs)
        return result