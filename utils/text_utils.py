import re
from llama_index.core.node_parser import TokenTextSplitter

def clean_text(text: str) -> str:
    """
    Cleans OCR text by removing excessive whitespaces and newlines.
    """
    # Replace multiple spaces with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 256, chunk_overlap: int = 32) -> list[str]:
    """
    Splits text into chunks of `chunk_size` tokens with `chunk_overlap` tokens overlap.
    """
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    return chunks
