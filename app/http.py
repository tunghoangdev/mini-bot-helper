from __future__ import annotations

import logging
import time
from collections.abc import Callable

import requests

LOGGER = logging.getLogger(__name__)


def request_with_retry(
    request: Callable[[], requests.Response],
    *,
    retries: int,
    timeout: int,
    operation: str,
) -> requests.Response:
    """Retry transport errors and transient HTTP responses with bounded backoff."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = request()
        except (requests.RequestException, TimeoutError) as exc:
            last_error = exc
        else:
            if response.status_code < 400:
                return response
            if response.status_code not in {408, 429, 500, 502, 503, 504}:
                response.raise_for_status()
            detail = response.text.strip().replace("\n", " ")[:500]
            last_error = requests.HTTPError(
                f"{operation} returned HTTP {response.status_code}: {detail}",
                response=response,
            )
        if attempt == retries:
            break
        delay = min(2**attempt, 8)
        LOGGER.warning("%s failed; retrying in %ss", operation, delay)
        time.sleep(delay)
    assert last_error is not None
    raise last_error
