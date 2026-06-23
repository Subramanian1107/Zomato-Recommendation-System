from typing import Protocol, List, Dict, Any, Optional

class LLMClient(Protocol):
    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Asynchronously calls the LLM with messages and returns the text response."""
        ...
