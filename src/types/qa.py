from dataclasses import dataclass
from typing import Protocol


@dataclass
class QaPair:
    """A question-answer pair from a chat conversation."""

    question: str
    answer: str


class QaProcessor(Protocol):
    """Protocol defining the interface for Q&A processors."""

    async def __call__(self, user_id: int, qa_pairs: list[QaPair]) -> None:
        """Process the Q&A pairs for a given user.

        Args:
            user_id: The ID of the user whose Q&A pairs are being processed
            qa_pairs: List of question-answer pairs to process
        """
        ...
