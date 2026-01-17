import re
import os
import emoji
from bs4 import BeautifulSoup

# load slang dictionary
BASE_DIR = os.path.dirname(__file__)
SLANG_PATH = os.path.join(BASE_DIR, "slang.txt")

slang_dict = {}
with open(SLANG_PATH, encoding="utf-8") as f:
    for line in f:
        if ":" in line:
            k, v = line.strip().split(":", 1)
            slang_dict[k] = v


def preprocess_roberta(text: str) -> str:
    # lowercase
    text = text.lower()

    # remove html
    text = BeautifulSoup(text, "html.parser").get_text(" ")

    # remove url
    text = re.sub(r"http\S+|www\S+", "", text)

    # remove mention
    text = re.sub(r"@\w+", "", text)

    # remove hashtag symbol
    text = text.replace("#", "")

    # normalize repeated characters
    text = re.sub(r"(.)\1{2,}", r"\1", text)

    # normalize slang
    words = text.split()
    words = [slang_dict.get(w, w) for w in words]
    text = " ".join(words)

    # remove emoji
    text = emoji.replace_emoji(text, replace="")

    # remove non-alphanumeric chars
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", " ", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
