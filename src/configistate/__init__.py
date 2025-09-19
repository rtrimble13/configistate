"""
configistate - A useful config file utility.

This package provides a configuration file utility that supports TOML format
and file:// path variables.
"""

__version__ = "0.1.0"
__author__ = "rtrimble13"

from .config import Config

__all__ = ["Config"]
