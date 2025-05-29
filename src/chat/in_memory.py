from src import types


class InMemoryQuestionList(types.QuestionList):
    """
    In-memory sequencing of a fixed list of questions per user.
    """

    def __init__(self, questions: list[types.Question]) -> None:
        self._questions: list[types.Question] = questions
        # user_id → current question index
        self._indices: dict[int, int] = {}
        # user_id → list of answers provided so far
        self._answers: dict[int, list[str]] = {}

    async def has_user_started(self, user_id: int) -> bool:
        return user_id in self._indices

    async def current_question(self, user_id: int) -> types.Question | None:
        idx = self._indices.get(user_id, 0)
        if idx < len(self._questions):
            return self._questions[idx]
        return None

    async def advance(self, user_id: int, answer: str) -> None:
        # Initialize user data if not present
        if user_id not in self._indices:
            self._indices[user_id] = 0
            self._answers[user_id] = []

        # Only record and advance if there are questions remaining
        idx = self._indices[user_id]
        if idx < len(self._questions):
            self._answers[user_id].append(answer)
            self._indices[user_id] = idx + 1

    async def all_finished(self, user_id: int) -> bool:
        idx = self._indices.get(user_id, 0)
        return idx >= len(self._questions)

    async def qa_pairs(self, user_id: int) -> list[types.QaPair]:
        if not await self.has_user_started(user_id):
            return []
        idx = self._indices[user_id]
        return [
            types.QaPair(question=self._questions[i], answer=answer)
            for i, answer in enumerate(self._answers[user_id])
            if i < idx
        ]


class InMemoryUserAnswerStorage(types.UserAnswerStorage):
    """
    In-memory storage of in-progress answers per user.
    """

    def __init__(self) -> None:
        self._store: dict[int, str | None] = {}

    async def append(self, user_id: int, partial_answer: str) -> None:
        """
        Appends the draft response for a given user.
        """
        current = self._store.get(user_id)
        # Initialize or append with newline
        self._store[user_id] = (current + "\n" if current else "") + partial_answer

    async def get(self, user_id: int) -> str | None:
        """
        Retrieves the current draft response, if any.
        """
        return self._store.get(user_id)

    async def clear(self, user_id: int) -> None:
        """
        Removes any saved draft for the specified user.
        """
        self._store[user_id] = None
