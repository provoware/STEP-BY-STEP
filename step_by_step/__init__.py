"""STEP-BY-STEP modular dashboard tool."""

from .core.config_manager import ConfigManager, UserPreferences
from .core.startup import StartupManager

__all__ = ["ConfigManager", "UserPreferences", "StartupManager", "__version__"]

__version__ = "0.2.0"
