# configistate
A useful config file utility.

A configuration utility that provides a consistent, robust framework for incorporating configuration files in software projects.

## Features

- **Python Library**: Import `configistate` into your projects for programmatic config management
- **CLI Tool**: Use `confy` command-line tool for working with config files
- **TOML Support**: Full support for TOML configuration files
- **File Variables**: Support for `file://` path variables to read file contents
- **Aliases**: Define config file aliases in `~/.confy.rc` for easy access

## Installation

```bash
# Install from source
make build
make install

# Or install in development mode
make build
```

## Python Library Usage

```python
from configistate import Config

# Load a config file
config = Config('config.toml')

# Get values
database_host = config.get('database.host')
debug_mode = config.get('debug', False)

# Set values
config.set('database.port', 5432)
config.save()

# List sections and variables
sections = config.list_sections()
variables = config.list_variables('database')
```

### File Variables

Config files can reference external files using `file://` URLs:

```toml
[secrets]
api_key = "file:///path/to/secret.txt"
```

The library will automatically read the file content and substitute it as the variable value.

## CLI Tool Usage

The `confy` command provides a command-line interface:

```bash
# List all sections
confy config.toml --list

# List variables in a section
confy config.toml --list database

# Get a configuration value
confy config.toml --get database.host

# Set a configuration value
confy config.toml --set database.port 5432
```

### Aliases

Define aliases in `~/.confy.rc`:

```toml
[aliases]
myapp = "/path/to/myapp/config.toml"
```

Then use the alias:

```bash
confy myapp --get database.host
```

## Development

```bash
# Setup development environment
make build

# Run tests
make test

# Run linting
make fmt

# Build documentation
make doc

# Create distribution package
make dist
```

## Requirements

- Python 3.8+
- TOML support

## License

MIT License - see LICENSE file for details.
