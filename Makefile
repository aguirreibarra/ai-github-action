.PHONY: mypy
mypy: 
	poetry run mypy src tests

.PHONY: tests
test:
	poetry run pytest tests
