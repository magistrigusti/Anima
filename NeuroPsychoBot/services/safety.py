CRISIS_PATTERNS = (
    "не хочу жить",
    "хочу умереть",
    "хочу сдохнуть",
    "убью себя",
    "убить себя",
    "покончу с собой",
    "покончить с собой",
    "наложить на себя руки",
    "суицид",
    "самоубий",
    "свести счеты",
    "свести счёты",
    "порезать вены",
    "выйти в окно",
    "прыгнуть с крыши",
    "kill myself",
    "suicide",
    "end my life",
    "i want to die",
)


def has_crisis_signal(text: str) -> bool:
    normalized_text = text.lower()

    return any(pattern in normalized_text for pattern in CRISIS_PATTERNS)
