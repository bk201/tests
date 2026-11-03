"""
Base class for SupportBundle operations.
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Abstract base for SupportBundle implementations."""

    @abstractmethod
    def create(self, name, description):
        """Create a SupportBundle CR in harvester-system."""
        pass

    @abstractmethod
    def wait_for_state(self, name, state, timeout):
        """Wait until the SupportBundle reaches the state; fail on the error state."""
        pass

    @abstractmethod
    def delete_if_exists(self, name):
        """Delete a SupportBundle CR and wait until it's gone; silently ignores 404."""
        pass
