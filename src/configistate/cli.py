"""
Command-line interface for the configistate library.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

import click
import toml

from .config import Config


def load_aliases() -> Dict[str, str]:
    """
    Load aliases from ~/.confy.rc file.

    Returns:
        Dictionary mapping alias names to config file paths.
    """
    confy_rc_path = Path.home() / ".confy.rc"

    if not confy_rc_path.exists():
        return {}

    try:
        with open(confy_rc_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        return data.get("aliases", {})
    except Exception as e:
        click.echo(
            f"Warning: Could not load aliases from {confy_rc_path}: {e}",
            err=True,
        )
        return {}


def resolve_config_path(config_arg: str) -> str:
    """
    Resolve config file path, handling aliases.

    Args:
        config_arg: Config file path or alias name.

    Returns:
        Resolved config file path.
    """
    aliases = load_aliases()

    if config_arg in aliases:
        return aliases[config_arg]

    return config_arg


def handle_list_command(config: Config, section: Optional[str] = None) -> None:
    """
    Handle the --list command.

    Args:
        config: Config object.
        section: Optional section name to list variables for.
    """
    if section:
        variables = config.list_variables(section)
        if variables:
            click.echo(f"Variables in section '{section}':")
            for var in variables:
                click.echo(f"  {var}")
        else:
            click.echo(
                f"No variables found in section '{section}' "
                "or section does not exist."
            )
    else:
        sections = config.list_sections()
        if sections:
            click.echo("Sections:")
            for section in sections:
                click.echo(f"  {section}")
        else:
            click.echo("No sections found.")


def handle_get_command(config: Config, key: str) -> None:
    """
    Handle the --get command.

    Args:
        config: Config object.
        key: Configuration key to get.
    """
    value = config.get(key)
    if value is not None:
        click.echo(value)
    else:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)


def handle_set_command(config: Config, key: str, value: str) -> None:
    """
    Handle the --set command.

    Args:
        config: Config object.
        key: Configuration key to set.
        value: Value to set.
    """
    config.set(key, value)
    config.save()
    click.echo(f"Set '{key}' = '{value}'")


@click.command()
@click.argument("config_file")
@click.option(
    "-l",
    "--list",
    "list_flag",
    is_flag=True,
    help="List all sections",
)
@click.option(
    "-g", "--get", "get_key", help="Get the value of a configuration key"
)
@click.option(
    "-s",
    "--set",
    "set_values",
    nargs=2,
    help="Set a configuration key to a value (KEY VALUE)",
)
@click.argument("section", required=False)
def main(config_file, list_flag, get_key, set_values, section):
    """Config file utility tool.

    CONFIG_FILE: Path to config file or alias name
    SECTION: Optional section name when using --list
    """
    # Count how many actions were provided
    actions_provided = sum(
        [list_flag, get_key is not None, set_values is not None]
    )

    if actions_provided == 0:
        click.echo(
            "Error: Exactly one of --list, --get, or --set must be specified.",
            err=True,
        )
        sys.exit(1)
    elif actions_provided > 1:
        click.echo(
            "Error: Exactly one of --list, --get, or --set must be specified.",
            err=True,
        )
        sys.exit(1)

    # For --list, the section can be provided as a positional argument
    if list_flag and section and (get_key or set_values):
        click.echo(
            "Error: Section argument can only be used with --list.", err=True
        )
        sys.exit(1)

    # Resolve config file path (handle aliases)
    config_path = resolve_config_path(config_file)

    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config(config_path)
        elif set_values:
            # For set operations, create a new config if file doesn't exist
            config = Config()
            config.config_path = Path(config_path)
        else:
            # For other operations, the file must exist
            click.echo(
                f"Error: Configuration file not found: {config_path}",
                err=True,
            )
            sys.exit(1)

        # Handle the requested action
        if list_flag:
            handle_list_command(config, section)
        elif get_key:
            handle_get_command(config, get_key)
        elif set_values:
            key, value = set_values
            handle_set_command(config, key, value)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
