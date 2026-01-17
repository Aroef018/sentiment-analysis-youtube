# app/services/preprocessing_service.py

import re
from pathlib import Path


class PreprocessingService:
    def __init__(self):
        self.slang_dict = self._load_slang_dict()

    def _load_slang_dict(self) -> dict:
        slang_path = Path("app/slang.txt")
        slang_dict = {}

        if slang_path.exists():
            with open(slang_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        slang, formal = line.strip().split("=")
                        slang_dict[slang] = formal

        return slang_dict

    def _remove_url(self, text: str) -> str:
        return re.sub(r"http\S+|www\S+", "", text)

    def _remove_mention_hashtag(self, text: str) -> str:
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"#\w+", "", text)
        return text

    def _remove_emoji(self, text: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub("", text)

    def _normalize_repeated_chars(self, text: str) -> str:
        """Reduce repeated characters to avoid sparse tokens.

        - letters/digits: reduce runs longer than 2 to exactly 2 (e.g. "hellooo" -> "helloo")
        - punctuation: collapse repeated punctuation to single (e.g. "!!!" -> "!")
        """
        # letters and digits: reduce >2 repeats to 2
        text = re.sub(r"([A-Za-z0-9])\1{2,}", r"\1\1", text)
        # punctuation: collapse repeated punctuation to single
        text = re.sub(r"([!?.,])\1+", r"\1", text)
        return text

    def _remove_non_alphabet(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z\s]", " ", text)

    def _normalize_slang(self, text: str) -> str:
        words = text.split()
        normalized_words = [
            self.slang_dict.get(word, word) for word in words
        ]
        return " ".join(normalized_words)

    def clean_text(self, text: str) -> str:
        text = text.lower()
        text = self._remove_url(text)
        text = self._remove_mention_hashtag(text)
        text = self._remove_emoji(text)
        text = self._normalize_repeated_chars(text)
        text = self._remove_non_alphabet(text)
        text = self._normalize_slang(text)
        text = re.sub(r"\s+", " ", text).strip()

        return text
