import os

from openai import OpenAI


class Agent:
    
    def __init__(
        self,
        *,
        instructions: str,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.instructions = instructions
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        self._initilized = False

    def _initialize(self) -> None:
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = self.base_url or os.getenv("OPENAI_API_BASE_URL")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._initilized = True

    def chat(
        self,
        user_input: str,
        instructions_prefix: str | None = None,
        output_type=None,
        temperature: float = 0,
        **kwargs,
    ) -> str:
        if not self._initilized:
            self._initialize()

        instructions = self.instructions
        if instructions_prefix is not None:
            instructions = instructions_prefix + instructions

        messages = [
            {
                "role": "system",
                "content": instructions,
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        if output_type is None:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=4096,
                **kwargs,
            )
            return completion.choices[0].message.content
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
            response_format=output_type,
            **kwargs,
        )
        return completion.choices[0].message.parsed
