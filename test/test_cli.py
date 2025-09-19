"""
Tests for the CLI functionality.
"""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
import toml

from configistate.cli import load_aliases, main, resolve_config_path


class TestCLI:
    """Test cases for the CLI functionality."""

    def test_load_aliases(self):
        """Test loading aliases from ~/.confy.rc."""
        # Create a temporary .confy.rc file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump(
                {
                    "aliases": {
                        "config1": "/path/to/config1.toml",
                        "config2": "/path/to/config2.toml",
                    }
                },
                f,
            )
            confy_rc_path = f.name

        try:
            with patch("configistate.cli.Path.home") as mock_home:
                mock_home.return_value = Path(confy_rc_path).parent
                with patch("configistate.cli.Path.exists") as mock_exists:
                    mock_exists.return_value = True
                    with patch("builtins.open", open):
                        # Mock the path to point to our test file
                        with patch(
                            "configistate.cli.Path.__truediv__"
                        ) as mock_div:
                            mock_div.return_value = Path(confy_rc_path)
                            aliases = load_aliases()

            assert "config1" in aliases
            assert aliases["config1"] == "/path/to/config1.toml"
        finally:
            Path(confy_rc_path).unlink()

    def test_resolve_config_path_with_alias(self):
        """Test resolving config path with aliases."""
        with patch("configistate.cli.load_aliases") as mock_load:
            mock_load.return_value = {"config1": "/path/to/config1.toml"}

            assert resolve_config_path("config1") == "/path/to/config1.toml"
            assert (
                resolve_config_path("/direct/path.toml") == "/direct/path.toml"
            )

    def test_cli_list_sections(self):
        """Test CLI list command for sections."""
        # Create a test config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump(
                {
                    "database": {"host": "localhost", "port": 5432},
                    "cache": {"redis_url": "redis://localhost"},
                },
                f,
            )
            config_path = f.name

        try:
            # Capture stdout
            with patch("sys.argv", ["confy", config_path, "--list"]):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()
                    output = mock_stdout.getvalue()

            assert "Sections:" in output
            assert "database" in output
            assert "cache" in output
        finally:
            Path(config_path).unlink()

    def test_cli_list_variables(self):
        """Test CLI list command for variables in a section."""
        # Create a test config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump({"database": {"host": "localhost", "port": 5432}}, f)
            config_path = f.name

        try:
            # Capture stdout
            with patch(
                "sys.argv", ["confy", config_path, "--list", "database"]
            ):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()
                    output = mock_stdout.getvalue()

            assert "Variables in section" in output
            assert "host" in output
            assert "port" in output
        finally:
            Path(config_path).unlink()

    def test_cli_get_value(self):
        """Test CLI get command."""
        # Create a test config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump({"database": {"host": "localhost", "port": 5432}}, f)
            config_path = f.name

        try:
            # Test getting a value
            with patch(
                "sys.argv", ["confy", config_path, "--get", "database.host"]
            ):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()
                    output = mock_stdout.getvalue().strip()

            assert output == "localhost"
        finally:
            Path(config_path).unlink()

    def test_cli_set_value(self):
        """Test CLI set command."""
        # Create a test config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            toml.dump({"database": {"host": "localhost"}}, f)
            config_path = f.name

        try:
            # Test setting a value
            with patch(
                "sys.argv",
                ["confy", config_path, "--set", "database.port", "5432"],
            ):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()
                    output = mock_stdout.getvalue()

            assert "Set 'database.port' = '5432'" in output

            # Verify the value was actually set
            with patch(
                "sys.argv", ["confy", config_path, "--get", "database.port"]
            ):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    main()
                    output = mock_stdout.getvalue().strip()

            assert output == "5432"
        finally:
            Path(config_path).unlink()

    def test_cli_nonexistent_file(self):
        """Test CLI with nonexistent config file."""
        with patch(
            "sys.argv", ["confy", "/nonexistent/config.toml", "--list"]
        ):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1
                assert "Configuration file not found" in mock_stderr.getvalue()
