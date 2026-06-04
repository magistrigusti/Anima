from anima.services.nvidia_client import ChatMessage, ChatRole


class DialogueMemory:
    def __init__(self, max_messages: int) -> None:
        self._max_messages = max(2, max_messages)
        self._storage: dict[int, list[ChatMessage]] = {}

    def get_history(self, user_id: int) -> list[ChatMessage]:
        return list(self._storage.get(user_id, []))

    def remember_user_message(self, user_id: int, text: str) -> None:
        self._remember(user_id=user_id, role="user", content=text)

    def remember_assistant_message(self, user_id: int, text: str) -> None:
        self._remember(user_id=user_id, role="assistant", content=text)

    def clear(self, user_id: int) -> None:
        self._storage.pop(user_id, None)

    def _remember(self, user_id: int, role: ChatRole, content: str) -> None:
        history = self._storage.setdefault(user_id, [])
        history.append({"role": role, "content": content})

        if len(history) > self._max_messages:
            self._storage[user_id] = history[-self._max_messages :]
