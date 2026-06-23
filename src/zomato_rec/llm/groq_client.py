import logging
import asyncio
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from zomato_rec.config import Settings

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.GROQ_API_KEY
        self._client: Optional[AsyncGroq] = None

    def _get_client(self) -> AsyncGroq:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your environment or .env file.")
        if self._client is None:
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call Groq chat completion API with optional JSON mode, retries, and timeouts."""
        client = self._get_client()
        model = self.settings.LLM_MODEL
        timeout = self.settings.LLM_TIMEOUT_SECONDS
        max_retries = self.settings.LLM_MAX_RETRIES

        attempts = 0
        last_err = None
        while attempts <= max_retries:
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "timeout": float(timeout),
                }
                if response_format:
                    kwargs["response_format"] = response_format

                logger.info(f"Calling Groq completion with model={model}, attempt={attempts+1}...")
                response = await client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except Exception as e:
                attempts += 1
                last_err = e
                logger.warning(f"Groq API call attempt {attempts} failed: {e}")
                if attempts <= max_retries:
                    await asyncio.sleep(1 * attempts)

        logger.error(f"Groq API call failed after {max_retries + 1} attempts.")
        raise last_err
