FILES=

tests-unit:
	poetry run coverage run --source=steam_trade_bot --branch -m pytest tests/unit
	poetry run coverage report -m

tests-int:
	poetry run coverage run --source=steam_trade_bot --branch -m pytest tests/integration
	poetry run coverage report -m

tests: tests-unit tests-int

lint:
	poetry run pylint --rcfile pyproject.toml --fail-under 8 steam_trade_bot $(FILES)

mypy:
	poetry run mypy --ignore-missing-imports steam_trade_bot $(FILES)

format:
	poetry run black steam_trade_bot tests $(FILES)

format-check:
	poetry run black --check steam_trade_bot tests $(FILES)

ci: tests lint mypy format
