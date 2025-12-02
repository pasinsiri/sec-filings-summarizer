from config import GROK_API_KEY, GROK_MODEL, FILING_TYPE, MAX_CHUNKS

def chunk_text(text, max_tokens=8000):
    """Simple chunking by characters (good enough + fast)"""
    words = text.split()
    chunks = []
    current = []
    current_tokens = 0

    for word in words:
        word_tokens = len(word) // 4 + 1
        if current_tokens + word_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            current = [word]
            current_tokens = word_tokens
        else:
            current.append(word)
            current_tokens += word_tokens
    if current:
        chunks.append(" ".join(current))
    return chunks[:MAX_CHUNKS]  # limit to avoid explosion