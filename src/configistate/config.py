"""
Core configuration handling functionality.
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Prefer stdlib tomllib for reading (Python 3.11+),
# fall back to third-party 'toml'.
try:
    import tomllib as _tomllib  # type: ignore
except Exception:
    _tomllib = None

try:
    # third-party toml (used for writing and as fallback reader)
    import toml as _toml
except Exception:
    _toml = None


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
        self._file_mappings: Dict[str, Path] = (
            {}
        )  # Maps config keys to file paths

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

        # Use stdlib tomllib (binary file) when available,
        # otherwise use third-party toml (text).
        if _tomllib is not None:
            with open(self.config_path, "rb") as f:
                self._data = _tomllib.load(f)
        elif _toml is not None:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._data = _toml.load(f)
        else:
            raise ImportError(
                "No TOML parser available. Install the 'toml' "
                "package (pip install toml) "
                "or run on Python 3.11+ which provides tomllib."
            )

        # Clear any existing file mappings and process file:// variables
        self._file_mappings.clear()
        self._process_file_variables(self._data, [])

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

        if _toml is None:
            raise ImportError(
                "Saving TOML requires the third-party 'toml' "
                "package. Install it (pip install toml)."
            )

        # Save file-based variables back to their original files
        self._save_file_variables()

        # Create a copy of data with file:// references restored for TOML save
        save_data = self._prepare_data_for_save()

        with open(save_path, "w", encoding="utf-8") as f:
            _toml.dump(save_data, f)

        self.config_path = save_path

    def _save_file_variables(self) -> None:
        """
        Save file-based variables back to their original files.
        """
        for config_key, file_path in self._file_mappings.items():
            try:
                # Get the current value from the config
                current_value = self.get(config_key)
                if current_value is not None:
                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write the value back to the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(str(current_value))
            except Exception as e:
                print(f"Warning: Could not write to file {file_path}: {e}")

    def _prepare_data_for_save(self) -> Dict[str, Any]:
        """
        Prepare configuration data for saving, restoring file:// references.

        Returns:
            Configuration data with file:// references restored.
        """
        # Deep copy the data to avoid modifying the original
        import copy

        save_data = copy.deepcopy(self._data)

        # Restore file:// references for variables that were loaded from files
        for config_key, file_path in self._file_mappings.items():
            keys = config_key.split(".")
            current = save_data

            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k in current and isinstance(current[k], dict):
                    current = current[k]
                else:
                    # Path doesn't exist, skip this mapping
                    break
            else:
                # Restore the file:// reference
                final_key = keys[-1]
                if final_key in current:
                    # Make path relative to config file if needed
                    if self.config_path and file_path.is_absolute():
                        try:
                            rel_path = file_path.relative_to(
                                self.config_path.parent
                            )
                            current[final_key] = f"file://{rel_path}"
                        except ValueError:
                            # Path is not relative to config dir, use absolute
                            current[final_key] = f"file://{file_path}"
                    else:
                        current[final_key] = f"file://{file_path}"

        return save_data

    def _process_file_variables(
        self, data: Dict[str, Any], key_path: list
    ) -> None:
        """
        Process file:// variables in the configuration data.

        Args:
            data: Configuration data dictionary to process.
            key_path: Current path in the configuration hierarchy.
        """
        for key, value in data.items():
            current_key_path = key_path + [key]
            if isinstance(value, dict):
                self._process_file_variables(value, current_key_path)
            elif isinstance(value, str) and value.startswith("file://"):
                # Parse the file:// URL and read the file content
                file_path_str = re.sub(r"^file://", "", value)
                file_path = Path(file_path_str).expanduser()

                # Make path relative to config file if it's not absolute
                if not file_path.is_absolute() and self.config_path:
                    file_path = self.config_path.parent / file_path

                # Store the mapping from config key to file path
                config_key = ".".join(current_key_path)
                self._file_mappings[config_key] = file_path

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
