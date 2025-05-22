from tortoise import Tortoise

from src.persistence.models import User, PartialAnswer, QAEntry
from src.chat import UserAnswerStorage, QuestionList, Question, QaPair


class TortoiseUserAnswerStorage(UserAnswerStorage):
    async def append(self, user_id: int, partial_answer: str) -> None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await User.filter(id=user_id).first()
        existing = await PartialAnswer.filter(user=user).first()
        if existing:
            existing.content += f"\n{partial_answer}"
            await existing.save()
        else:
            await PartialAnswer.create(user=user, content=partial_answer)

    async def get(self, user_id: int) -> str | None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await User.filter(id=user_id).first()
        entry = await PartialAnswer.filter(user=user).first()
        return entry.content if entry else None

    async def clear(self, user_id: int) -> None:
        await PartialAnswer.filter(user_id=user_id).delete()


class TortoiseQuestionList(QuestionList):
    def __init__(self, questions: list[Question]):
        self.questions = questions

    async def has_user_started(self, user_id: int) -> bool:
        return await QAEntry.filter(user_id=user_id).exists()

    async def current_question(self, user_id: int) -> Question | None:
        if not await User.filter(id=user_id).exists():
            return self.questions[0] if self.questions else None

        answered = await QAEntry.filter(user_id=user_id).count()
        if answered >= len(self.questions):
            return None
        return self.questions[answered]

    async def advance(self, user_id: int, answer: str) -> None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await User.filter(id=user_id).first()
        answered = await QAEntry.filter(user=user).count()
        if answered < len(self.questions):
            q = self.questions[answered]
            await QAEntry.create(
                user=user,
                question_index=answered,
                question_text=q.text,
                answer=answer,
            )

    async def all_finished(self, user_id: int) -> bool:
        count = await QAEntry.filter(user_id=user_id).count()
        return count >= len(self.questions)

    async def qa_pairs(self, user_id: int) -> list[QaPair]:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        entries = await QAEntry.filter(user_id=user_id).order_by("question_index").all()
        pairs: list[QaPair] = []
        for entry in entries:
            idx = entry.question_index
            original_q = self.questions[idx]
            pairs.append(
                QaPair(
                    question=Question(
                        text=entry.question_text,
                        answer_requirement=original_q.answer_requirement,
                    ),
                    answer=entry.answer,
                )
            )
        return pairs


async def init_db(
    db_url: str,
    models: list[str],
) -> None:
    await Tortoise.init(
        db_url=db_url,
        modules={"models": models},
    )
    await Tortoise.generate_schemas()
