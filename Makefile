.PHONY: test tdd

test:
	uv run pytest --cov=src --cov-report term-missing:skip-covered --cov-branch

tdd:
	uv run ptw . --cov=src --cov-report term-missing:skip-covered --cov-branch
