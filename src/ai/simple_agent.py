from dataclasses import dataclass, field
from typing import Any, Callable
import os

from openai import AsyncOpenAI

DEFAULT_MODEL_SETTINGS = dict(
    temperature=0,
    max_tokens=4096,
    model="gpt-4o",
)


@dataclass(kw_only=True)
class SimpleAgent:
    """
    A simple agent that uses OpenAI's chat completion API to generate responses
    based on a set of instructions and a model name.
    """

    instructions: str
    """
    Instructions for the agent to follow when generating responses.
    """

    expand_query: Callable | None = None
    """
    Callable that enriches user input with additional context.
    """

    model_settings: dict = field(default_factory=lambda: DEFAULT_MODEL_SETTINGS)
    """
    Model settings (e.g., temperature, max tokens).
    """

    output_type: Any | None = None
    """
    If specified, the expected output type for structured responses.
    """

    api_key: str | None = None
    """
    OpenAI API key (defaults to environment variable if unset).
    """

    base_url: str | None = None
    """
    OpenAI API endpoint URL (defaults to environment variable if unset).
    """

    @property
    def client(self) -> AsyncOpenAI:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        base_url = self.base_url or os.getenv("OPENAI_API_BASE_URL")
        return AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def __call__(self, user_input: str, **query_expansion_kwargs) -> str:
        """
        Send user input through the agent to produce a response.

        :param user_input: User’s message to process.
        :param query_expansion_kwargs: Arguments for the expand_query function, if used.

        :return: The generated response from the agent.
        """
        if self.expand_query:
            user_input = self.expand_query(user_input, **query_expansion_kwargs)

        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_input},
        ]

        model_settings = DEFAULT_MODEL_SETTINGS | self.model_settings
        params = dict(
            messages=messages,
            **model_settings,
        )

        if self.output_type is None:
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content

        params["response_format"] = self.output_type
        response = await self.client.beta.chat.completions.parse(**params)
        return response.choices[0].message.parsed
