import datetime

from src.chat import info_extractor


def flatten_user_info(
    user_name: str,
    tg: str,
    user_info: info_extractor.UserInformation,
    started_at: datetime.datetime,
) -> dict:
    """Flatten UserInformation for Google Sheets row.

    Args:
        user_name: Name of the user
        tg: Telegram URL of the user
        user_info: UserInformation object containing all user data

    Returns:
        Dictionary with flattened user information ready for Google Sheets
    """
    return {
        "user_name": user_name,
        "tg": tg,
        # Corporate accounts (comma-separated bank names)
        "accounts": ", ".join([acc.bank_name for acc in user_info.accounts]),
        # PSPs (comma-separated psp_name)
        "psps": ", ".join([psp.psp_name for psp in user_info.psps]),
        # PSP logins (comma-separated)
        "psp_logins": ", ".join([psp.login for psp in user_info.psps]),
        # PSP passwords (comma-separated)
        "psp_passwords": ", ".join([psp.password for psp in user_info.psps]),
        # PSP details (comma-separated)
        "psp_details": ", ".join([psp.details or "" for psp in user_info.psps]),
        # Company details (main)
        "company_name": user_info.company_details.name,
        "company_address": user_info.company_details.address,
        "company_phone": user_info.company_details.phone,
        "company_email": user_info.company_details.email,
        # Business activities
        "business_activities": user_info.business_activities.activities,
        # Hosting info
        "has_website": str(user_info.hosting.has_website),
        "hosting_access_details": user_info.hosting.access_details or "",
        # Profit sharing
        "profit_sharing": user_info.profit_sharing.agreement,
        # Security verification
        "security_verification": user_info.security_verification.agreement,
        # Creation timestamp
        "created_at": datetime.date.today().isoformat(),
        "user_started_at": started_at.date().isoformat(),
    }
