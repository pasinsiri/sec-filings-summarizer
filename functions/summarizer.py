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

def summarize_with_grok(text, client, is_final=False):
    if is_final:
        system_prompt = "You are a senior financial analyst. Summarize the key points from multiple section summaries into one concise, investor-friendly 10-K summary (max 800 words). Include: business overview, growth strategy, key risks, financial highlights, and forward outlook."
        user_prompt = text
    else:
        system_prompt = "You are a financial analyst. Summarize this section of a 10-K filing in 250–350 words. Focus on business strategy, competitive position, risks, and financial implications. Be concise but insightful."
        user_prompt = f"Section text:\n\n{text}"

    response = client.chat.completions.create(
        model=GROK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1024 if is_final else 512
    )
    return response.choices[0].message.content.strip()