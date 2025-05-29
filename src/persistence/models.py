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


class SuperGroup(Model):
    id = fields.IntField(pk=True)
    group_id = fields.BigIntField(
        unique=True
    )  # Telegram group IDs can be large numbers

    class Meta:
        table = "super_groups"


class TopicGroup(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="topics")
    topic_group_id = (
        fields.BigIntField()
    )  # Telegram topic/thread IDs can be large numbers

    class Meta:
        table = "topic_groups"
        indexes = [("user",), ("topic_group_id",)]


class Manager(Model):
    id = fields.IntField(pk=True)
    manager_link = fields.TextField()

    class Meta:
        table = "managers"


class UserManager(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="user_managers", on_delete=fields.CASCADE
    )
    manager_link = fields.TextField()

    class Meta:
        table = "user_managers"
        indexes = [("user",)]
