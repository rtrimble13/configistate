"""
Command-line interface for the configistate library.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

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
        print(
            f"Warning: Could not load aliases from {confy_rc_path}: {e}",
            file=sys.stderr,
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
            print(f"Variables in section '{section}':")
            for var in variables:
                print(f"  {var}")
        else:
            print(
                f"No variables found in section '{section}' "
                "or section does not exist."
            )
    else:
        sections = config.list_sections()
        if sections:
            print("Sections:")
            for section in sections:
                print(f"  {section}")
        else:
            print("No sections found.")


def handle_get_command(config: Config, key: str) -> None:
    """
    Handle the --get command.

    Args:
        config: Config object.
        key: Configuration key to get.
    """
    value = config.get(key)
    if value is not None:
        print(value)
    else:
        print(f"Key '{key}' not found.", file=sys.stderr)
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
    print(f"Set '{key}' = '{value}'")


def main():
    """Main entry point for the confy CLI."""
    parser = argparse.ArgumentParser(
        description="Config file utility tool", prog="confy"
    )

    parser.add_argument(
        "config_file", help="Path to config file or alias name"
    )

    # Create a mutually exclusive group for the main actions
    action_group = parser.add_mutually_exclusive_group(required=True)

    action_group.add_argument(
        "-l",
        "--list",
        nargs="?",
        const="",
        metavar="SECTION",
        help="List all sections (default) or variables in a section",
    )

    action_group.add_argument(
        "-g",
        "--get",
        metavar="KEY",
        help="Get the value of a configuration key",
    )

    action_group.add_argument(
        "-s",
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set a configuration key to a value",
    )

    args = parser.parse_args()

    # Resolve config file path (handle aliases)
    config_path = resolve_config_path(args.config_file)

    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config(config_path)
        elif args.set:
            # For set operations, create a new config if file doesn't exist
            config = Config()
            config.config_path = Path(config_path)
        else:
            # For other operations, the file must exist
            print(
                f"Error: Configuration file not found: {config_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Handle the requested action
        if args.list is not None:
            section = args.list if args.list else None
            handle_list_command(config, section)
        elif args.get:
            handle_get_command(config, args.get)
        elif args.set:
            key, value = args.set
            handle_set_command(config, key, value)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
