from typing import Optional
from fastapi import UploadFile
import requests


def extract_from_file(file: UploadFile) -> str:
    # Minimal placeholder: read raw text-ish content
    content = file.file.read()
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_from_url(url: str) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_from_youtube(url: str) -> str:
    # Stub: plug in Whisper / yt-dlp here
    return f"Transcript placeholder for: {url}"


def extract_source(source_url: Optional[str], file: Optional[UploadFile]) -> str:
    if file is not None:
        return extract_from_file(file)
    if source_url is None:
        return ""
    if "youtube.com" in source_url or "youtu.be" in source_url:
        return extract_from_youtube(source_url)
    return extract_from_url(source_url)
