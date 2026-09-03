import unicodedata
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedDocument:
    document_id: str
    filename: str
    media_type: str
    size_bytes: int
    language_hint: str | None
    text: str
    stored_path: str


class DocumentProcessingError(ValueError):
    """Raised when a supported document cannot be extracted."""


class DocumentService:
    def __init__(self, raw_dir: Path | str = "data/raw") -> None:
        self.raw_dir = Path(raw_dir)

    def save_and_extract(
        self,
        *,
        filename: str,
        content: bytes,
        media_type: str,
        language_hint: str | None,
    ) -> ExtractedDocument:
        suffix = Path(filename).suffix.lower()
        if suffix not in {".txt", ".pdf"}:
            raise DocumentProcessingError("Only .txt and .pdf files are supported.")
        if not content:
            raise DocumentProcessingError("The uploaded document is empty.")

        document_id = str(uuid4())
        safe_name = Path(filename).name
        stored_file = self.raw_dir / f"{document_id}_{safe_name}"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        stored_file.write_bytes(content)

        try:
            text = self._extract_text(stored_file, suffix)
        except Exception as exc:
            stored_file.unlink(missing_ok=True)
            raise DocumentProcessingError("The document could not be processed.") from exc

        text = unicodedata.normalize("NFC", text)
        if not text.strip():
            stored_file.unlink(missing_ok=True)
            raise DocumentProcessingError("The document contains no extractable text.")

        return ExtractedDocument(
            document_id=document_id,
            filename=safe_name,
            media_type=media_type,
            size_bytes=len(content),
            language_hint=language_hint,
            text=text,
            stored_path=str(stored_file),
        )

    @staticmethod
    def _extract_text(file_path: Path, suffix: str) -> str:
        if suffix == ".txt":
            return file_path.read_text(encoding="utf-8-sig")

        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)