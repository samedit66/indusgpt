from typing import Literal

from pydantic import BaseModel, Field
from agents import Agent, ModelSettings


def create_faq_agent(
    model_name: str,
    model_settings: ModelSettings,
) -> Agent:
    ...
