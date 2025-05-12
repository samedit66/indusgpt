from __future__ import annotations
from dataclasses import dataclass


class ChatContext:
    """
    A simple FSM‑style context manager for sequential questions.
    """

    def __init__(self, questions: list[Question]) -> None:
        # Remaining questions queue
        self._questions: list[Question] = list(questions)
        # Mapping from question index → {"question": str, "answer": str}
        self._data: dict[int, dict[str, str]] = {}

    def record_answer(self, answer: str) -> None:
        """
        Record the answer for the current question and pop it off the queue.
        """
        if not self._questions:
            raise RuntimeError("No active question to answer.")

        idx = len(self._data)
        self._data[idx] = {
            "question": self.current_question.text,
            "answer": answer,
        }
        self._prepare_next_question()

    def get_answers(self) -> list[dict[str, str]]:
        """
        Return a list of all recorded Q&A pairs, in the order asked.
        """
        return [self._data[i] for i in sorted(self._data)]

    @property
    def current_question(self) -> Question | None:
        """
        Return the next pending question, or None if all are answered.
        """
        return self._questions[0] if self._questions else None

    @property
    def next_question(self) -> Question | None:
        return self._questions[1] if len(self._questions) >= 2 else None

    def _prepare_next_question(self) -> None:
        """
        Discard the current question (called after recording its answer).
        """
        if self._questions:
            self._questions.pop(0)

    def has_more_questions(self) -> bool:
        """
        Return True if there are still questions left.
        """
        return bool(self._questions)


@dataclass(frozen=True, slots=True)
class Question:
    text: str
    requirement: str


def default_context() -> ChatContext:
    questions_data = [
        {
            "question": "User greets you or wants to start conversation.",
            "val_rule": "User greets you or wants to start conversation.",
        },
        {
            "question": ("Do you have corporate (business) accounts? In which banks?"),
            "val_rule": (
                "User response **must** confirm that they have a corporate/business bank account "
                "and say the bank name.\nExamples:\n"
                "- I have a corporate account in Sber bank.\n"
                "- I got a business account in Bank of Baroda."
            ),
        },
        {
            "question": (
                "Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?"
            ),
            "val_rule": (
                "User response **must** include the name of the **PSP** to which their corporate account "
                "is connected.\nExamples:\n"
                "- Yes my account is connected to Razorpay.\n"
                "- Yes it is PayU.\n"
                "- My PSP is Gatepay."
            ),
        },
        {
            "question": "Can you provide login and password access to the PSP account?",
            "val_rule": (
                "User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to "
                "**share login credentials**.\nCollect any additional information user may provide about their PSP account.\n"
                "Examples:\n"
                "- Yes, my login is admin, password is 123341."
            ),
        },
        {
            "question": (
                "Do you already have a website approved by the PSP?\n"
                "If yes — please give us hosting access (we may need to adjust code or API)\n"
                "If not — we will create the website ourselves"
            ),
            "val_rule": (
                "User response **must** answer “yes” or “no.” If “yes,” they **must** mention they can "
                'provide **hosting access**. If "no", only "no" is required.\nExamples:\n'
                "- No.\n"
                "- Yes. Next goes any details about hosting access."
            ),
        },
        {
            "question": (
                "Are you open to working under a profit‑sharing model (5% of transaction volume) instead of a one‑time deal?"
            ),
            "val_rule": (
                'User response **must** clearly say "yes" or "no".\nExamples:\n'
                "- Yes.\n"
                "- No.\n"
                "- Of course\n"
                "- Sure."
            ),
        },
    ]

    questions = [
        Question(text=item["question"], requirement=item["val_rule"])
        for item in questions_data
    ]
    return ChatContext(questions)
