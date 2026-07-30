"""Resolve a Buddian page into a public, direct MP4 URL."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class VideoExtractionError(ValueError):
    """Raised when a safe direct video URL cannot be found."""


_MP4_PATTERN = re.compile(
    r"(?:https?:)?(?:\\/|/)[^\"'<>\\s]+?\.mp4(?:\?[^\"'<>\\s]*)?",
    re.IGNORECASE,
)


def _is_public_http_url(url: str) -> bool:
    """Reject non-HTTP and private/local destinations before fetching them."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror:
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            return False
    return True


def _is_mp4_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".mp4")


def _normalise_candidate(candidate: str, page_url: str) -> str:
    return urljoin(page_url, candidate.replace("\\/", "/"))


def _fetch_public_page(source_url: str, timeout: float) -> requests.Response:
    """Fetch a page while validating every redirect destination."""
    current_url = source_url
    for _ in range(6):
        try:
            response = requests.get(
                current_url,
                timeout=timeout,
                allow_redirects=False,
                headers={"User-Agent": "Validator/1.0 (+https://validator.prampta.com)"},
            )
        except requests.RequestException as exc:
            raise VideoExtractionError(f"Could not fetch the video page: {exc}") from exc
        if response.is_redirect:
            location = response.headers.get("Location")
            if not location:
                raise VideoExtractionError("The video page returned an invalid redirect.")
            current_url = urljoin(current_url, location)
            if not _is_public_http_url(current_url):
                raise VideoExtractionError("The video page redirected to a non-public location.")
            continue
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise VideoExtractionError(f"Could not fetch the video page: {exc}") from exc
        return response
    raise VideoExtractionError("The video page redirected too many times.")


def extract_mp4_url(video_url: str, *, timeout: float = 15) -> str:
    """Return a direct MP4 URL from a direct URL or a Buddian video page.

    Only public HTTP(S) locations are fetched, preventing this UI from being used
    as a server-side request forgery proxy.
    """
    source_url = video_url.strip()
    if not source_url:
        raise VideoExtractionError("Enter a Buddian video page URL or a direct .mp4 URL.")
    if not _is_public_http_url(source_url):
        raise VideoExtractionError("The video URL must be a publicly reachable HTTP(S) URL.")
    if _is_mp4_url(source_url):
        return source_url

    response = _fetch_public_page(source_url, timeout)

    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[str] = []
    for tag in soup.find_all(["video", "source"]):
        if src := tag.get("src"):
            candidates.append(src)
    candidates.extend(match.group(0) for match in _MP4_PATTERN.finditer(response.text))

    for candidate in candidates:
        resolved = _normalise_candidate(candidate, response.url)
        if _is_mp4_url(resolved) and _is_public_http_url(resolved):
            return resolved

    raise VideoExtractionError(
        "No direct .mp4 source was found on that page. Use a public direct MP4 URL instead."
    )
