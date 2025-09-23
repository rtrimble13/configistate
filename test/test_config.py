"""
Tests for the Config class.
"""

import tempfile
from pathlib import Path

import pytest
import toml

from configistate import Config


class TestConfig:
    """Test cases for the Config class."""

    def test_init_empty(self):
        """Test initializing an empty Config object."""
        config = Config()
        assert config.config_path is None
        assert config.data == {}

    def test_load_simple_config(self):
        """Test loading a simple TOML config file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump(
                {
                    "database": {"host": "localhost", "port": 5432},
                    "debug": True,
                },
                f,
            )
            config_path = f.name

        try:
            config = Config(config_path)

            assert config.get("database.host") == "localhost"
            assert config.get("database.port") == 5432
            assert config.get("debug") is True
            assert config.get("nonexistent", "default") == "default"
        finally:
            Path(config_path).unlink()

    def test_file_variable_support(self):
        """Test file:// variable support."""
        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False
        ) as content_file:
            content_file.write("secret_value_123")
            content_path = content_file.name

        # Create a config file that references the content file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as config_file:
            toml.dump(
                {"secrets": {"api_key": f"file://{content_path}"}}, config_file
            )
            config_path = config_file.name

        try:
            config = Config(config_path)

            assert config.get("secrets.api_key") == "secret_value_123"
        finally:
            Path(config_path).unlink()
            Path(content_path).unlink()

    def test_set_and_get(self):
        """Test setting and getting configuration values."""
        config = Config()

        config.set("database.host", "localhost")
        config.set("database.port", 5432)
        config.set("debug", True)

        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config.get("debug") is True

    def test_list_sections(self):
        """Test listing sections."""
        config = Config()

        config.set("database.host", "localhost")
        config.set("cache.redis_url", "redis://localhost")
        config.set("debug", True)

        sections = config.list_sections()
        assert "database" in sections
        assert "cache" in sections
        assert "debug" not in sections  # debug is not a section

    def test_list_variables(self):
        """Test listing variables in a section."""
        config = Config()

        config.set("database.host", "localhost")
        config.set("database.port", 5432)
        config.set("debug", True)

        db_vars = config.list_variables("database")
        assert "host" in db_vars
        assert "port" in db_vars

        top_level_vars = config.list_variables()
        assert "debug" in top_level_vars

    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config()

        config.set("database.host", "localhost")
        config.set("database.port", 5432)
        config.set("debug", True)

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            config_path = f.name

        try:
            config.save(config_path)

            # Load the saved config and verify
            new_config = Config(config_path)
            assert new_config.get("database.host") == "localhost"
            assert new_config.get("database.port") == 5432
            assert new_config.get("debug") is True
        finally:
            Path(config_path).unlink()

    def test_save_file_variables(self):
        """Test saving file-based variables back to their original files."""
        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False
        ) as content_file:
            content_file.write("original_secret")
            content_path = content_file.name

        # Create a config file that references the content file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as config_file:
            toml.dump(
                {
                    "secrets": {"api_key": f"file://{content_path}"},
                    "database": {"host": "localhost"},
                },
                config_file,
            )
            config_path = config_file.name

        try:
            # Load the config
            config = Config(config_path)

            # Verify the file content was loaded
            assert config.get("secrets.api_key") == "original_secret"

            # Modify the file-based variable
            config.set("secrets.api_key", "new_secret_value")

            # Also modify a non-file variable
            config.set("database.port", 5432)

            # Save the config
            config.save()

            # Verify the content file was updated
            with open(content_path, "r", encoding="utf-8") as f:
                assert f.read() == "new_secret_value"

            # Verify the main config file still has the file:// reference
            with open(config_path, "r", encoding="utf-8") as f:
                saved_config = toml.load(f)

            assert saved_config["secrets"]["api_key"].startswith("file://")
            assert saved_config["database"]["host"] == "localhost"
            assert saved_config["database"]["port"] == 5432

            # Verify loading the saved config works correctly
            new_config = Config(config_path)
            assert new_config.get("secrets.api_key") == "new_secret_value"
            assert new_config.get("database.host") == "localhost"
            assert new_config.get("database.port") == 5432

        finally:
            Path(config_path).unlink()
            Path(content_path).unlink()

    def test_save_file_variables_relative_path(self):
        """Test saving file-based variables with relative paths."""
        # Create a temporary directory structure
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()

            # Create a content file in a subdirectory
            secrets_dir = config_dir / "secrets"
            secrets_dir.mkdir()
            content_path = secrets_dir / "api_key.txt"
            content_path.write_text("relative_secret")

            # Create a config file with relative path reference
            config_path = config_dir / "app.toml"
            config_data = {
                "app": {"name": "myapp"},
                "secrets": {"api_key": "file://secrets/api_key.txt"},
            }
            with open(config_path, "w") as f:
                toml.dump(config_data, f)

            # Load and modify the config
            config = Config(config_path)
            assert config.get("secrets.api_key") == "relative_secret"

            config.set("secrets.api_key", "new_relative_secret")
            config.save()

            # Verify the content file was updated
            assert content_path.read_text() == "new_relative_secret"

            # Verify the config file still has relative reference
            with open(config_path, "r") as f:
                saved_config = toml.load(f)
            assert (
                saved_config["secrets"]["api_key"]
                == "file://secrets/api_key.txt"
            )

            # Verify reloading works
            new_config = Config(config_path)
            assert new_config.get("secrets.api_key") == "new_relative_secret"

    def test_nonexistent_file(self):
        """Test handling of nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            Config("/nonexistent/path/config.toml")
