"""
Helm release CRD Implementation - reads the release from Helm's storage Secrets.
"""
import base64
import gzip
import json

from kubernetes import client

from helm_release.base import Base
from utility.utility import logging

GZIP_MAGIC = b"\x1f\x8b"


def merge_values(defaults, overrides):
    """Merge user-supplied values over chart defaults like Helm does: maps merge
    recursively, other values replace the default, and null removes the key."""
    merged = dict(defaults)
    for key, value in overrides.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_values(merged[key], value)
        else:
            merged[key] = value
    return merged


class CRD(Base):
    """Reads Helm releases from the sh.helm.release.v1.* Secrets in the release namespace."""

    def __init__(self):
        self.core_api = client.CoreV1Api()

    def _get_release(self, namespace, release):
        secrets = self.core_api.list_namespaced_secret(
            namespace, label_selector=f"owner=helm,name={release},status=deployed").items
        if not secrets:
            raise AssertionError(f"No deployed Helm release {namespace}/{release}")
        latest = max(secrets, key=lambda s: int(s.metadata.labels.get("version", "0")))
        # Secret data is base64-encoded by Kubernetes, and Helm base64-encodes the
        # (usually gzipped) release JSON before storing it.
        data = base64.b64decode(base64.b64decode(latest.data["release"]))
        if data[:2] == GZIP_MAGIC:
            data = gzip.decompress(data)
        logging(f"Read Helm release {namespace}/{release} from secret {latest.metadata.name}")
        return json.loads(data)

    def get_values(self, namespace, release):
        # Subchart defaults aren't stored in the release, so this only covers the
        # parent chart's defaults, plus everything the user supplied.
        rel = self._get_release(namespace, release)
        defaults = rel.get("chart", {}).get("values") or {}
        return merge_values(defaults, rel.get("config") or {})
