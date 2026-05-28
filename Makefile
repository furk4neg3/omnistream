.PHONY: format test lint compose-up compose-producer compose-down compose-logs

format:
	@echo "format step coming soon"

lint:
	@echo "lint step coming soon"

test:
	@echo "test step coming soon"

compose-up:
	docker compose up --build

compose-producer:
	docker compose --profile producer run --rm producer

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f
