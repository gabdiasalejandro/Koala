from pathlib import Path


def load_input_text(file_name: str) -> str:
    file_path = Path(file_name)

    if not file_path.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {file_path}")

    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8")

    if file_path.suffix.lower() == ".docx":
        from docx import Document

        doc = Document(str(file_path))
        lines = [paragraph.text.rstrip() for paragraph in doc.paragraphs]
        return "\n".join(lines)

    raise ValueError("Formato no soportado. Usa .txt o .docx")
