from types import ModuleType

from NeuroPsychoBot.texts import en, ru


TEXT_PACKS: dict[str, ModuleType] = {
    "ru": ru,
    "en": en,
}


def get_texts(language: str) -> ModuleType:
    return TEXT_PACKS.get(language, ru)
