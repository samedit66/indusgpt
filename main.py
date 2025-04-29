import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Model,
    ModelProvider,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    set_tracing_disabled,
)

from instructions.router import create_router


load_dotenv()

BASE_URL = os.getenv("OPENAI_API_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("GEMMA")


client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(True)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


CUSTOM_MODEL_PROVIDER = CustomModelProvider()

agent = create_router(
    model_name=os.environ["GEMMA"], model_settings=ModelSettings(temperature=0.0)
)

while True:
    user_input = input("USER: ")
    result = Runner.run_sync(
        agent,
        user_input,
        run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER),
    )
    print("MODEL:", result.final_output)
