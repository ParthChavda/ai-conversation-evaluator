from app.models.schemas import Conversation


class ConversationNormalizer:
    def normalize(self, conversation: Conversation) -> Conversation:
        normalized_turns = [
            turn.model_copy(update={"text": " ".join(turn.text.strip().split())})
            for turn in conversation.turns
        ]
        return conversation.model_copy(update={"turns": normalized_turns})
