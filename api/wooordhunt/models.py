from typing import TypedDict


class Example(TypedDict):
    """
    Пример использования слова в предложении
    """

    example: str
    translate: str | None


class DictionaryEntry(TypedDict):
    """
    Ответ API с данными слова для изучения
    """

    word: str
    transcription: str | None
    translation: str | None
    examples: list[Example]
