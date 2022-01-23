import requests
import pypandoc
from readability import Document

SPEC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
}


def get_document(url: str, headers: dict = SPEC_HEADERS, **kwargs) -> Document:
    r"""Generates a structured minimal document of a web page.

    Use:
    .title() for title,
    .summary() for trimmed down readable html document,
    and some other methods."""

    return Document(requests.get(url, headers=headers, **kwargs).text)


def html_to_md(
    html_text: str, format: str = "html-native_divs-native_spans", *args
) -> str:
    return pypandoc.convert_text(source=html_text, to="md", format=format, *args)

# Don't LAUGH!
