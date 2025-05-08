from __future__ import annotations
from typing import Literal, Optional

from pydantic import BaseModel, Field, SecretStr

from src.agent import Agent


QUERY_TEMPLATE = """
Extract the following user-provided information into JSON matching the IntegrationSetup schema.
User text:
{}
"""


class InfoExtactor:
    def __init__(self, **kwargs) -> None:
        self._extractor = Agent(
            instructions="""
You are a data extraction assistant. Parse the user text to populate the IntegrationSetup structure exactly.
Return a JSON object with keys: accounts, psps, hosting, profit_sharing.
- accounts: list of corporate accounts (bank_name)
- psps: list of PSP connections (psp_name, login, password)
- hosting: has_website (bool) and access_details (string or null)
- profit_sharing: agreement ("yes")
""",
            **kwargs,
        )

    def extract(self, text_information: str) -> IntegrationSetup:
        information = self._extractor.chat(
            user_input=QUERY_TEMPLATE.format(text_information)
        )
        return information


class IntegrationSetup(BaseModel):
    accounts: list[CorporateAccount] = Field(
        ..., description="List of corporate bank accounts."
    )
    psps: list[PSPAccount] = Field(..., description="List of connected PSPs.")
    hosting: HostingInfo
    profit_sharing: ProfitSharingAgreement


class CorporateAccount(BaseModel):
    bank_name: str = Field(..., description="Bank name where the corporate account is.")


class PSPAccount(BaseModel):
    psp_name: str = Field(
        ..., description="Name of the PSP to which the bank account is connected."
    )
    login: str = Field(..., description="Login to the PSP account.")
    password: SecretStr = Field(..., description="Password to the PSP account.")


class HostingInfo(BaseModel):
    has_website: bool = Field(
        ...,
        description="Whether the user already has an approved website with the PSP.",
    )
    access_details: Optional[SecretStr] = Field(
        None,
        description="Hosting credentials or URL to access and adjust code/API. Required if has_website is True.",
    )


class ProfitSharingAgreement(BaseModel):
    agreement: Literal["yes"] = Field(
        ...,
        description="User agreement to work under a profit-sharing model instead of a one-time deal.",
    )
