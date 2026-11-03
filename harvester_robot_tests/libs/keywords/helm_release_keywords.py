"""
Helm Release Keywords - creates HelmRelease() instance and delegates - NO direct API calls!
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa: E402

from utility.utility import logging  # noqa: E402
from helm_release import HelmRelease  # noqa: E402


def format_tag(tag):
    """Format an image tag like Harvester's settings.Image.GetTag(): numeric tags
    lose trailing zeros, e.g. 16.0 -> "16"."""
    if isinstance(tag, bool) or tag is None:
        return "" if tag is None else str(tag)
    if isinstance(tag, (int, float)):
        return format(Decimal(repr(tag)).normalize(), "f")
    return str(tag)


class helm_release_keywords:
    """Layer 3: Helm release keyword wrapper."""

    def __init__(self):
        self.helm_release = HelmRelease()

    def get_helm_release_value(self, namespace, release, path):
        """Return the value at the dotted path of a release's values, chart defaults
        included; fails if the path doesn't exist."""
        value = self.helm_release.get_values(namespace, release)
        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                raise AssertionError(f"{path} not found in Helm release {namespace}/{release}")
            value = value[key]
        return value

    def get_helm_release_image(self, namespace, release, path, registry=""):
        """Return the image at the dotted path as {repository, tag, imagePullPolicy, image},
        where image is [<registry>/]<repository>:<tag>."""
        value = self.get_helm_release_value(namespace, release, path)
        repository = value.get("repository", "")
        tag = format_tag(value.get("tag"))
        image = f"{repository}:{tag}"
        if registry:
            image = f"{registry}/{image}"
        logging(f"Helm release {namespace}/{release} {path}: {image}")
        return {
            "repository": repository,
            "tag": tag,
            "imagePullPolicy": value.get("imagePullPolicy", ""),
            "image": image,
        }
