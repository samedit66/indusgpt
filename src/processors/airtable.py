import pyairtable

from src import types
from src.chat import info_extractor
from src.persistence import models
from src.processors import utils


class AirtableProcessor:
    """Processor that writes Q&A data to Airtable."""

    def __init__(self, access_token: str, base_id: str, table_id: str) -> None:
        self.api = pyairtable.Api(access_token)
        self.table = self.api.table(base_id, table_id)

    async def __call__(self, user_id: int, qa_pairs: list[types.QaPair]):
        user_name = (await models.User.filter(id=user_id).first()).name
        tg = (await models.User.filter(id=user_id).first()).url
        user_info = await info_extractor.extract_info(qa_pairs)
        row = utils.flatten_user_info(user_name, tg, user_info)
        self.table.create(row)
