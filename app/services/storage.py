from app.models.schemas import Conversation, EvaluationResult


class InMemoryEvaluationStore:
    """Repository boundary that can be replaced with SQLAlchemy or document storage."""

    def __init__(self):
        self._conversations: dict[str, Conversation] = {}
        self._evaluations_by_conversation: dict[str, EvaluationResult] = {}

    def save(self, conversation: Conversation, result: EvaluationResult) -> None:
        self._conversations[conversation.conversation_id] = conversation
        self._evaluations_by_conversation[conversation.conversation_id] = result

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def get_result(self, conversation_id: str) -> EvaluationResult | None:
        return self._evaluations_by_conversation.get(conversation_id)
