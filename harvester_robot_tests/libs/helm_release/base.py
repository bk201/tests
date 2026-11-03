"""
Base class for Helm release operations.
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Abstract base for HelmRelease implementations."""

    @abstractmethod
    def get_values(self, namespace, release):
        """Return the release's values, chart defaults included, like `helm get values -a`."""
        pass
