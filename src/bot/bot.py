from src.router.router import Router
from src.faq_agent import FAQAgent
from src.bot.question_validator import QuestionValidator


class Bot:
    
    def __init__(self, **kwargs) -> None:
        self._router = Router(**kwargs)
        self._faq_agent = FAQAgent(**kwargs)
        self._qvalidator = QuestionValidator(**kwargs)

    def respond(self, user_input: str, question: str | None = None) -> str:
        user_intent = self._router.classify(user_input)

        match user_intent.category:
            case "faq":
                return self._faq_agent.respond(user_input)
            case "information":
                question = "Do you have corporate accounts? In which banks?"
                validation_result = self._qvalidator.validate(user_input, question)
                return validation_result
