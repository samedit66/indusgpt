from .question_list import QuestionList, Question, QaPair
from .user_answer_storage import UserAnswerStorage


class InMemoryQuestionList(QuestionList):
    """
    In-memory sequencing of a fixed list of questions per user.
    """

    def __init__(self, questions: list[Question]) -> None:
        self._questions: list[Question] = questions
        # user_id → current question index
        self._indices: dict[int, int] = {}
        # user_id → list of answers provided so far
        self._answers: dict[int, list[str]] = {}

    def register_user(self, user_id: int) -> None:
        self._indices[user_id] = 0
        self._answers[user_id] = []

    def delete_user(self, user_id: int) -> None:
        self._indices.pop(user_id, None)
        self._answers.pop(user_id, None)

    def contains_user(self, user_id: int) -> bool:
        return user_id in self._indices

    def current_question(self, user_id: int) -> Question | None:
        idx = self._indices.get(user_id, 0)
        if idx < len(self._questions):
            return self._questions[idx]
        return None

    def forth(self, user_id: int, answer: str) -> None:
        if not self.contains_user(user_id):
            # auto-register if needed
            self.register_user(user_id)
        idx = self._indices[user_id]
        # record answer and advance
        self._answers[user_id].append(answer)
        self._indices[user_id] = idx + 1

    def all_finished(self, user_id: int) -> bool:
        idx = self._indices.get(user_id, 0)
        return idx >= len(self._questions)

    def qa_pairs(self, user_id: int) -> list[QaPair]:
        if not self.contains_user(user_id):
            return []
        idx = self._indices[user_id]
        return [
            QaPair(question=self._questions[i], answer=answer)
            for i, answer in enumerate(self._answers[user_id])
            if i < idx
        ]


class InMemoryUserAnswerStorage(UserAnswerStorage):
    """
    In-memory storage of in-progress answers per user.
    """

    def __init__(self) -> None:
        self._store: dict[int, str | None] = {}

    def register_user(self, user_id: int) -> None:
        self._store[user_id] = None

    def delete_user(self, user_id: int) -> None:
        self._store.pop(user_id, None)

    def contains_user(self, user_id: int) -> bool:
        return user_id in self._store

    def append(self, user_id: int, partial_answer: str) -> None:
        if not self.contains_user(user_id):
            self.register_user(user_id)
        current = self._store[user_id]
        # start fresh if no draft yet
        self._store[user_id] = (current or "") + partial_answer

    def get(self, user_id: int) -> str | None:
        return self._store.get(user_id)

    def clear(self, user_id: int) -> None:
        if self.contains_user(user_id):
            self._store[user_id] = None
