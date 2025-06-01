from abc import ABC, abstractmethod


class Context(ABC):
    """
    Defines the interface for storing, retrieving, and clearing a context.
    Mainly used to make bot learn new information without need to edit the code or
    already given instructions.
    """

    @abstractmethod
    async def append(self, information: str) -> None:
        """
        Appends to the context.

        :param information: the latest text to add to context
        """

    @abstractmethod
    async def get(self) -> str | None:
        """
        Retrieves the current context, if any.

        :return: the stored context (None if nothing was stored)
        """

    @abstractmethod
    async def clear(self) -> None:
        """
        Removes any saved context.
        """
