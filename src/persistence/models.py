from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()

    class Meta:
        table = "user"


class PartialAnswer(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="partial", on_delete=fields.CASCADE
    )
    content = fields.TextField()

    class Meta:
        table = "partial_answer"
        indexes = [("user",)]


class QAEntry(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="entries", on_delete=fields.CASCADE
    )
    question_index = fields.IntField()
    question_text = fields.TextField()
    answer = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "qa_entry"
        indexes = [("user", "question_index")]
