.PHONY: format test lint aws-readiness-check compose-up compose-producer compose-down compose-logs

format:
	@echo "format step coming soon"

lint: aws-readiness-check

aws-readiness-check:
	bash scripts/check_aws_readiness.sh

test:
	bash scripts/run_tests.sh

compose-up:
	docker compose up --build

compose-producer:
	docker compose --profile producer run --rm producer

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f
