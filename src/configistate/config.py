"""
Core configuration handling functionality.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import toml


class Config:
    """
    A configuration class that supports TOML files and file:// path variables.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the Config object.

        Args:
            config_path: Path to the configuration file.
                        If None, no file is loaded.
        """
        self.config_path = Path(config_path) if config_path else None
        self._data: Dict[str, Any] = {}

        if self.config_path:
            self.load(self.config_path)

    def load(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from a TOML file.

        Args:
            config_path: Path to the TOML configuration file.
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._data = toml.load(f)

        # Process file:// variables
        self._process_file_variables(self._data)

    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to a TOML file.

        Args:
            config_path: Path to save the configuration.
                        If None, uses the loaded path.
        """
        save_path = Path(config_path) if config_path else self.config_path

        if not save_path:
            raise ValueError("No configuration path specified")

        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            toml.dump(self._data, f)

        self.config_path = save_path

    def _process_file_variables(self, data: Dict[str, Any]) -> None:
        """
        Process file:// variables in the configuration data.

        Args:
            data: Configuration data dictionary to process.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                self._process_file_variables(value)
            elif isinstance(value, str) and value.startswith("file://"):
                # Parse the file:// URL and read the file content
                parsed = urlparse(value)
                file_path = Path(parsed.path)

                # Make path relative to config file if it's not absolute
                if not file_path.is_absolute() and self.config_path:
                    file_path = self.config_path.parent / file_path

                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data[key] = f.read().strip()
                    except Exception as e:
                        # Keep original value if file can't be read
                        print(f"Warning: Could not read file {file_path}: {e}")
                else:
                    print(f"Warning: File not found: {file_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation
                 like 'section.variable').
            default: Default value if key is not found.

        Returns:
            Configuration value or default.
        """
        keys = key.split(".")
        current = self._data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports dot notation
                 like 'section.variable').
            value: Value to set.
        """
        keys = key.split(".")
        current = self._data

        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value

    def list_sections(self) -> list:
        """
        List all sections in the configuration.

        Returns:
            List of section names.
        """
        return [
            key for key, value in self._data.items() if isinstance(value, dict)
        ]

    def list_variables(self, section: Optional[str] = None) -> list:
        """
        List variables in a section or all top-level variables.

        Args:
            section: Section name. If None, lists top-level variables.

        Returns:
            List of variable names.
        """
        if section:
            section_data = self.get(section, {})
            if isinstance(section_data, dict):
                return list(section_data.keys())
            return []
        else:
            return [
                key
                for key, value in self._data.items()
                if not isinstance(value, dict)
            ]

    @property
    def data(self) -> Dict[str, Any]:
        """Get the raw configuration data."""
        return self._data.copy()
