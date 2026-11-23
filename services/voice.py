"""Nepali text-to-speech using the female Nepali neural voice."""
import asyncio
from pathlib import Path

DEFAULT_VOICE = "ne-NP-HemkalaNeural"


async def _save_speech_async(text, output_path, voice):
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+0%",
        volume="+0%",
    )
    await communicate.save(str(output_path))


def create_speech(text, output_path, voice=DEFAULT_VOICE):
    """Generate MP3 narration. Requires internet access to the Edge TTS service."""
    clean_text = " ".join(str(text or "").split()).strip()
    if not clean_text:
        raise ValueError("Cannot create narration: the meme caption is empty.")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_save_speech_async(clean_text, output_path, voice))
    if not output_path.exists() or output_path.stat().st_size < 1000:
        raise RuntimeError("Nepali speech generation returned an empty audio file.")
    return output_path
