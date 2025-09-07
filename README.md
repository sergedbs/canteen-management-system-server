### First steps to run the project

1. Install `uv`, see [installation instruction](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the project
3. `cd` into the project's folder and install python requirements: ```uv sync```
4. Install pre-commit hooks: ```uv run pre-commit install```
5. Run ```docker compose up -w```
6. To add new dependencies ```uv add dependency_name``` & ```uv lock```
