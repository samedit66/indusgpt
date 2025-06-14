from src.persistence import models
from src import types


class TortoiseUserAnswerStorage(types.UserAnswerStorage):
    async def append(self, user_id: int, partial_answer: str) -> None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await models.User.filter(id=user_id).first()
        existing = await models.PartialAnswer.filter(user=user).first()
        if existing:
            existing.content += f"{partial_answer}"
            await existing.save()
        else:
            await models.PartialAnswer.create(user=user, content=partial_answer)

    async def get(self, user_id: int) -> str | None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await models.User.filter(id=user_id).first()
        entry = await models.PartialAnswer.filter(user=user).first()
        return entry.content if entry else None

    async def clear(self, user_id: int) -> None:
        await models.PartialAnswer.filter(user_id=user_id).delete()

    async def replace(self, user_id: int, new_answer: str) -> None:
        user = await models.User.filter(id=user_id).first()
        existing = await models.PartialAnswer.filter(user=user).first()
        if existing:
            existing.content = new_answer
            await existing.save()
        else:
            await models.PartialAnswer.create(user=user, content=new_answer)


class TortoiseQuestionList(types.QuestionList):
    def __init__(self, questions: list[types.Question]):
        self.questions = questions

    async def has_user_started(self, user_id: int) -> bool:
        return await models.QAEntry.filter(user_id=user_id).exists()

    async def current_question(self, user_id: int) -> types.Question | None:
        if not await models.User.filter(id=user_id).exists():
            return self.questions[0] if self.questions else None

        answered = await models.QAEntry.filter(user_id=user_id).count()
        if answered >= len(self.questions):
            return None
        return self.questions[answered]

    async def advance(self, user_id: int, answer: str) -> None:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        user = await models.User.filter(id=user_id).first()
        answered = await models.QAEntry.filter(user=user).count()
        if answered < len(self.questions):
            q = self.questions[answered]
            await models.QAEntry.create(
                user=user,
                question_index=answered,
                question_text=q.text,
                answer=answer,
            )

    async def all_finished(self, user_id: int) -> bool:
        user = await models.User.filter(id=user_id).first()
        count = await models.QAEntry.filter(user_id=user_id).count()
        return count >= len(self.questions) or user.is_onboarding_completed

    async def qa_pairs(self, user_id: int) -> list[types.QaPair]:
        # We do not check if the user exists, because
        # it must exist by the time we call this method
        entries = (
            await models.QAEntry.filter(user_id=user_id)
            .order_by("question_index")
            .all()
        )
        pairs: list[types.QaPair] = []
        for entry in entries:
            idx = entry.question_index
            original_q = self.questions[idx]
            pairs.append(
                types.QaPair(
                    question=types.Question(
                        text=entry.question_text,
                        answer_requirement=original_q.answer_requirement,
                    ),
                    answer=entry.answer,
                )
            )
        return pairs

    async def stop_talking_with(self, user_id: int) -> None:
        user = await models.User.filter(id=user_id).first()
        user.is_onboarding_completed = True
        await user.save()


class TortoiseContext(types.Context):
    async def append(self, information: str) -> None:
        await models.Context.create(context=information)

    async def get(self) -> str | None:
        contexts = await models.Context.all()
        if not contexts:
            return None
        return " ".join(c.context for c in contexts)

    async def clear(self) -> None:
        await models.Context.all().delete()
