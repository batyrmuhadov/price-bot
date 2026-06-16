import time
import logging
from typing import Optional

import requests

from config import HEADERS

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_with_retry(session: requests.Session, url: str,
                     max_retries: int = 3, timeout: int = 20,
                     retry_backoff: int = 2) -> Optional[requests.Response]:
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
            logger.warning("%s returned status %s (attempt %d/%d)",
                           url, response.status_code, attempt + 1, max_retries)
        except requests.RequestException as e:
            logger.warning("Request error for %s: %s (attempt %d/%d)",
                           url, e, attempt + 1, max_retries)
        if attempt < max_retries - 1:
            time.sleep(retry_backoff ** attempt)
    return None
