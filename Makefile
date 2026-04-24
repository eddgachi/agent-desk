up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

backend-shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec frontend sh

psql:
	docker-compose exec postgres psql -U office -d office_sim