from app.services.chunking import chunk_text, detect_language


def test_chunking_preserves_overlap() -> None:
    chunks = chunk_text("one two three four five six", chunk_size=4, overlap=2)

    assert [chunk.text for chunk in chunks] == [
        "one two three four",
        "three four five six",
    ]


def test_bangla_unicode_and_language_detection() -> None:
    text = "বাংলা ভাষার নথি"
    assert chunk_text(text, chunk_size=10, overlap=2)[0].text == text
    assert detect_language(text) == "Bangla"
    assert detect_language("বাংলা English") == "Mixed"