
import time
import requests
from src.config import Config

config = Config()

DELAY = 1.0
TIMEOUT = 300

session = requests.Session()

def api_call(path, accept="application/json", **params):
    """Returns the HTTP response, or raise an exception on error.
    """

    auth = (config.gn_user, config.gn_password)
    time.sleep(DELAY)

    url = f"{config.gn_origin_url}/{path.lstrip('/')}"

    response = session.get(
        url,
        params=params,
        auth=auth,
        headers={"Accept": accept},
        timeout=TIMEOUT,
    )

    response.raise_for_status()
    return response
   
    response.raise_for_status()