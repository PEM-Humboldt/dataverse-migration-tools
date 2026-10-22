"""Read-only (GET) client for a GeoNetwork 3.x catalogue.

"""
import hashlib
import os
import time
from pathlib import Path

import requests


class GeoNetworkReader:
    """Read-only client for the GeoNetwork 3.x API, with HTTP Basic authentication.

    It has no method that sends POST, PUT or DELETE: no harvest code can modify
    the catalogue by mistake. GeoNetwork 3.x accepts HTTP Basic authentication for
    GET requests (checked in testGeonetwork on 2026-10-01: the admin account sees
    54 private records that an anonymous request does not return).
    """

    def __init__(self, base_url, user, password, delay=1.0, timeout=300):
        self.base_url = base_url.rstrip("/")     # e.g. https://…/geonetwork/srv
        self.delay = delay            # pause before each request (seconds)
        self.timeout = timeout        # a hanging request does not block the harvest
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.headers.update({"User-Agent": "dataverse-migration-tools (IAvH)"})
        self.n_requests = 0           # for the summary of each step

    def get(self, path, accept="application/json", **params):
        """GET after the pause; return the HTTP response, or raise an exception on error.

        `accept` is sent as the Accept header: several services answer HTTP 500 without it
        (/api/site) or choose the format from it (/api/records/<uuid>/formatters/xml).
        No retries: the caller records the error and moves on; running the step again
        requests only what is missing.
        """
        time.sleep(self.delay)
        self.n_requests += 1
        r = self.session.get(self.base_url + path, params=params,
                             headers={"Accept": accept}, timeout=self.timeout)
        r.raise_for_status()
        return r

    def get_json(self, path, **params):
        """Decoded JSON body of a GET (raises ValueError if the body is not JSON)."""
        return self.get(path, **params).json()

    def download(self, path, target, chunk_size=8 * 1024 * 1024):
        """Download a file to `target`, streamed in chunks; return (size in bytes, MD5).

        Not used by the harvest: for the transfer of the attachments (data files and preview
        images), later. Streamed because GeoNetwork attachments reach 2.1 GB (185 GB in total):
        the file is never held whole in memory. Writes to `<name>.part` and renames at the end (atomic).
        Checking the size against the attachment list is up to the caller (GeoNetwork gives
        no checksum).
        """
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".part")
        time.sleep(self.delay)
        self.n_requests += 1
        md5, size = hashlib.md5(), 0
        with self.session.get(self.base_url + path, stream=True, timeout=self.timeout) as r:
            r.raise_for_status()
            with open(tmp, "wb") as out:
                for chunk in r.iter_content(chunk_size=chunk_size):   # explicit size: the default is 1 byte
                    out.write(chunk)
                    md5.update(chunk)
                    size += len(chunk)
        os.replace(tmp, target)
        return size, md5.hexdigest()
