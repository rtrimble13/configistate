This project is a configuration utility meant to provide a consistent, robust framework for incorporating configuration files in software projects.

The two output of this project are `configistate`, a python library that can be imported into other projects, and `confy`, a cli tool for working with config files from the command line.

### Directory Structure
- `src`: source code files
- `test`: unit tests
- `etc`: project configuration
- `doc`: project documentation and man files

### Development chain
- `make build`: create the project environment and build project
- `make install`: install the project
- `make test`: run test suite with pytest
- `make fmt`: run linting checks with black, flake8 and isort
- `make doc`: build and install man files
- `make dist`: create pypi distribution package

### General guidelines for pull requests
- Maintain project integrity.
- Use best practices for developing python code.
- Write unit tests for all new features using pytest framework.
- Run linting checks before committing code.
- Document all features and provide examples as appropriate.
