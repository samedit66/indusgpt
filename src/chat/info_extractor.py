from __future__ import annotations
from typing import Optional, Literal

from pydantic import BaseModel, Field

from src import types

from .simple_agent import SimpleAgent


class UserInformation(BaseModel):
    accounts: list[CorporateAccount] = Field(
        ..., description="List of corporate bank accounts."
    )
    psps: list[PSPAccount] = Field(..., description="List of connected PSPs.")
    company_details: CompanyDetails = Field(..., description="Company details.")
    hosting: HostingInfo = Field(..., description="Hosting information.")
    profit_sharing: ProfitSharingAgreement = Field(
        ..., description="Profit-sharing agreement."
    )


class CorporateAccount(BaseModel):
    bank_name: str = Field(..., description="Bank name where the corporate account is.")


class PSPAccount(BaseModel):
    psp_name: str = Field(
        ..., description="Name of the PSP to which the bank account is connected."
    )
    login: str = Field(..., description="Login to the PSP account.")
    password: str = Field(..., description="Password to the PSP account.")
    details: Optional[str] = Field(
        ...,
        description="Any additional information the user mentions about their PSP.",
    )
    company: CompanyDetails = Field(
        ..., description="Details of the company linked to the PSP account."
    )


class CompanyDetails(BaseModel):
    name: str = Field(
        ...,
        description="Name of the company linked to the payment gateway account.",
    )
    address: str = Field(
        ...,
        description="Company's registered address.",
    )
    phone: str = Field(
        ...,
        description="Company's contact phone number.",
    )
    email: str = Field(
        ...,
        description="Company's contact email address.",
    )


class HostingInfo(BaseModel):
    has_website: bool = Field(
        ...,
        description="Whether the user already has an approved website with the PSP.",
    )
    access_details: Optional[str] = Field(
        None,
        description="Hosting credentials or URL to access and adjust code/API. Required if has_website is True.",
    )


class ProfitSharingAgreement(BaseModel):
    agreement: Literal["Yes."] = Field(
        ...,
        description="User agreement to work under a profit-sharing model instead of a one-time deal.",
    )


INSTRUCTIONS = """
You are a data extraction assistant.
Your job is to collect the following information from users' answers:
- Names of banks where the user has corporate accounts.
- Connected PSPs.
- Hostring information.
- Agreement to work under a profit-sharing model.
- Company details for each payment gateway–linked company (name, address, phone, email).
"""


def expand_query(user_input: str) -> str:
    return f"Extract information from the following Q&A pairs.:\n{user_input}"


info_extractor = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=UserInformation,
)


async def extract_info(qa_pairs: list[types.QaPair]) -> UserInformation:
    qa = "\n".join(f"Q: {q.question}\nA: {q.answer}\n" for q in qa_pairs)
    return await info_extractor(qa)
