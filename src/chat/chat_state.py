from collections import namedtuple
from enum import Enum, auto, unique


@unique
class StateType(Enum):
    FINISHED = auto()
    IN_PROGRESS = auto()


State = namedtuple("State", "type question partial_answer")
"""Chat state.
When `type == StateType.IN_PROGRESS` there are current question (`str`) for user and user's partial answer (`str`).
Otherwise (`type == StateType.FINISHED`), both question and user's answer are `None`.
"""
