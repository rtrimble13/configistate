"""
Tests for the CLI functionality.
"""

import toml
from click.testing import CliRunner

from configistate.cli import load_aliases, main, resolve_config_path


class TestCLI:
    """Test cases for the CLI functionality."""

    def test_load_aliases(self, tmp_path, monkeypatch):
        """Test loading aliases from ~/.confy.rc."""
        # Create a temporary .confy.rc file
        confy_rc_content = {
            "aliases": {
                "config1": "/path/to/config1.toml",
                "config2": "/path/to/config2.toml",
            }
        }
        confy_rc_path = tmp_path / ".confy.rc"
        with open(confy_rc_path, "w") as f:
            toml.dump(confy_rc_content, f)

        # Mock Path.home() to return our temp directory
        monkeypatch.setattr("configistate.cli.Path.home", lambda: tmp_path)

        aliases = load_aliases()
        assert "config1" in aliases
        assert aliases["config1"] == "/path/to/config1.toml"

    def test_resolve_config_path_with_alias(self, monkeypatch):
        """Test resolving config path with aliases."""

        def mock_load_aliases():
            return {"config1": "/path/to/config1.toml"}

        monkeypatch.setattr("configistate.cli.load_aliases", mock_load_aliases)

        assert resolve_config_path("config1") == "/path/to/config1.toml"
        assert resolve_config_path("/direct/path.toml") == "/direct/path.toml"

    def test_cli_list_sections(self, tmp_path):
        """Test CLI list command for sections."""
        # Create a test config file
        config_content = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"redis_url": "redis://localhost"},
        }
        config_path = tmp_path / "test.toml"
        with open(config_path, "w") as f:
            toml.dump(config_content, f)

        runner = CliRunner()
        result = runner.invoke(main, [str(config_path), "--list"])

        assert result.exit_code == 0
        assert "Sections:" in result.output
        assert "database" in result.output
        assert "cache" in result.output

    def test_cli_list_variables(self, tmp_path):
        """Test CLI list command for variables in a section."""
        # Create a test config file
        config_content = {"database": {"host": "localhost", "port": 5432}}
        config_path = tmp_path / "test.toml"
        with open(config_path, "w") as f:
            toml.dump(config_content, f)

        runner = CliRunner()
        result = runner.invoke(main, [str(config_path), "--list", "database"])

        assert result.exit_code == 0
        assert "Variables in section" in result.output
        assert "host" in result.output
        assert "port" in result.output

    def test_cli_get_value(self, tmp_path):
        """Test CLI get command."""
        # Create a test config file
        config_content = {"database": {"host": "localhost", "port": 5432}}
        config_path = tmp_path / "test.toml"
        with open(config_path, "w") as f:
            toml.dump(config_content, f)

        runner = CliRunner()
        result = runner.invoke(
            main, [str(config_path), "--get", "database.host"]
        )

        assert result.exit_code == 0
        assert result.output.strip() == "localhost"

    def test_cli_set_value(self, tmp_path):
        """Test CLI set command."""
        # Create a test config file
        config_content = {"database": {"host": "localhost"}}
        config_path = tmp_path / "test.toml"
        with open(config_path, "w") as f:
            toml.dump(config_content, f)

        runner = CliRunner()

        # Test setting a value
        result = runner.invoke(
            main, [str(config_path), "--set", "database.port", "5432"]
        )
        assert result.exit_code == 0
        assert "Set 'database.port' = '5432'" in result.output

        # Verify the value was actually set
        result = runner.invoke(
            main, [str(config_path), "--get", "database.port"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "5432"

    def test_cli_nonexistent_file(self):
        """Test CLI with nonexistent config file."""
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/config.toml", "--list"])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.output

    def test_cli_no_action_specified(self, tmp_path):
        """Test CLI when no action is specified."""
        config_path = tmp_path / "test.toml"
        config_path.write_text("[test]\nkey = 'value'")

        runner = CliRunner()
        result = runner.invoke(main, [str(config_path)])

        assert result.exit_code == 1
        assert (
            "Exactly one of --list, --get, or --set must be specified"
            in result.output
        )
