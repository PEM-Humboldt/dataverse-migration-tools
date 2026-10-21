"""Read-only (GET) client for a Dataverse installation.
"""
import hashlib
import os
import time
from pathlib import Path

import requests


class DataverseReader:
    """Read-only client for the Dataverse native API.

    It has no method that sends POST, PUT or DELETE: no harvest code can modify
    the source by mistake.
    """

    def __init__(self, base_url, token, delay=1.0, timeout=300):
        self.base_url = base_url.rstrip("/")
        self.delay = delay            # pause before each request (seconds)
        self.timeout = timeout        # a hanging request does not block the harvest
        self.session = requests.Session()
        self.session.headers.update({
            "X-Dataverse-key": token,
            "User-Agent": "dataverse-migration-tools (IAvH)",
        })
        self.n_requests = 0           # for the summary of each step

    def _get(self, path, **params):
        """GET after the pause; return the HTTP response, or raise an exception on error.

        No retries: the caller records the error and moves on; running the step again
        requests only what is missing.
        """
        time.sleep(self.delay)
        self.n_requests += 1
        r = self.session.get(self.base_url + path, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r

    def get(self, path, **params):
        """Full native API response ({"status": "OK", "data": ...}), to be saved as is.

        Raises RuntimeError if Dataverse answers {"status": "ERROR", "message": ...}.
        """
        body = self._get(path, **params).json()
        if body.get("status") != "OK":
            raise RuntimeError(f"{path}: {body.get('message')}")
        return body

    def get_data(self, path, **params):
        """Only the "data" part of the response."""
        return self.get(path, **params)["data"]

    def download(self, path, target, **params):
        """Download a file to `target` and return its MD5 checksum.
        """
        target = Path(target)
        content = self._get(path, **params).content
        tmp = target.with_name(target.name + ".part")
        tmp.write_bytes(content)
        os.replace(tmp, target)
        return hashlib.md5(content).hexdigest()
