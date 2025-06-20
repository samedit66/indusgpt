from datetime import date
from pyairtable import Table


class AirtableDailyTracker:
    """
    A tracker for daily "Clicked" and "Talked" counters in an Airtable table.

    Initializes with your Airtable API key, base ID, and table name.
    Provides methods to increment today's counters, creating a new record if needed.
    """

    def __init__(self, access_token: str, base_id: str, table_id: str):
        """
        :param api_key: Your Airtable API key
        :param base_id: Your Airtable base ID
        :param table_name: The name of the table to track
        """
        self.table = Table(access_token, base_id, table_id)

    def _get_latest_record(self):
        """
        Fetches the most recent record based on the "Date" field.
        Returns the record dict or None if no records exist.
        """
        records = self.table.all(sort=["-Date"], max_records=1)
        return records[0] if records else None

    def increase_clicked(self):
        """
        Increments the "Clicked" field for today's entry.
        Creates a new record if there isn't one for today, setting Clicked=1, Talked=0.
        """
        today_str = date.today().isoformat()
        latest = self._get_latest_record()

        if not latest or latest.get("fields", {}).get("Date") != today_str:
            # No record for today: create new
            self.table.create(
                {
                    "Date": today_str,
                    "Clicked": 1,
                    "Talked": 0,
                }
            )
        else:
            # Increment existing
            rec_id = latest["id"]
            old = int(latest["fields"].get("Clicked", 0))
            self.table.update(rec_id, {"Clicked": old + 1})

    def increase_talked(self):
        """
        Increments the "Talked" field for today's entry.
        Creates a new record if there isn't one for today, setting Clicked=0, Talked=1.
        """
        today_str = date.today().isoformat()
        latest = self._get_latest_record()

        if not latest or latest.get("fields", {}).get("Date") != today_str:
            # No record for today: create new
            self.table.create(
                {
                    "Date": today_str,
                    "Clicked": 0,
                    "Talked": 1,
                }
            )
        else:
            # Increment existing
            rec_id = latest["id"]
            old = int(latest["fields"].get("Talked", 0))
            self.table.update(rec_id, {"Talked": old + 1})
