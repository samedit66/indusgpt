from pyairtable import Table


class AirtableUsersCounter:
    """
    A users counter based on the Airtable table.

    Initializes with your Airtable API token, base ID, and table name/ID.
    Provides a method to increment the users_count field on the first record in the table,
    or create a new record if none exist.
    """

    def __init__(self, access_token: str, base_id: str, table_id: str):
        """
        :param access_token: Your Airtable API token
        :param base_id: Your Airtable base ID
        :param table_id: The name or ID of the table to update
        """
        self.table = Table(access_token, base_id, table_id)

    def increase_users_count(self):
        """
        Increments the "users_count" field on the first record of the table by 1.
        If the field is missing or empty, it initializes it to 1.
        If no records exist, creates a new record with users_count = 1.
        """
        # Fetch the first record in the table
        records = self.table.all(max_records=1)
        print(f"Da fuck? Records: {records}")

        if not records:
            # No record exists: create new with users_count = 1
            self.table.create({"users_count": 1})
            print("Where?")
            return

        record = records[0]
        rec_id = record["id"]

        # Get the existing users_count value or default to 0
        old_count = int(record.get("fields", {}).get("users_count", 0))

        # Update the record with the new count
        self.table.update(rec_id, {"users_count": old_count + 1})
        print("Or else where?")
