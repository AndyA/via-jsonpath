.PHONY: test tdd

test:
	uv run pytest --cov=src --cov-report term-missing:skip-covered --cov-branch

tdd:
	uv run ptw . --cov=src --cov-report term-missing:skip-covered --cov-branch

test-with-%:
	uv run --python $* pytest

test-versions: test-with-3.10 test-with-3.11 test-with-3.12 test-with-3.13