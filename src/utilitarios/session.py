
import time
import requests
from src.config import Config

config = Config()

DELAY = 1.0
TIMEOUT = 300

def api_call(path, accept="application/json", **params):
    """GET after the pause; return the HTTP response, or raise an exception on error.

    `accept` is sent as the Accept header: several services answer HTTP 500 without it
    (/api/site) or choose the format from it (/api/records/<uuid>/formatters/xml).
    No retries: the caller records the error and moves on; running the step again
    requests only what is missing.
    """
    time.sleep(DELAY)
    n_requests += 1

    url = f"{config.gn_origin_url}/{path.lstrip('/')}"

    session = requests.Session()
    response = session.get(
        url,
        params=params,
        headers={"Accept": accept},
        timeout=TIMEOUT,
    )
    
    response.raise_for_status()
    return response