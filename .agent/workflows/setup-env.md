---
description: Setup or repair the Python virtual environment
---

1. Ensure you are in the project root directory.
2. If there are issues with the current environment, optionally remove it:
```bash
pipenv --rm
```
3. Install dependencies from the Pipfile:
```bash
pipenv install
```
4. Verify the environment is active:
```bash
pipenv --venv
```