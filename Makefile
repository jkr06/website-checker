initdb:
	docker run --name postgres -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres:latest
	sleep 10
	python initdb.py
	
test:
	docker run --name postgres_test -e POSTGRES_PASSWORD=secret -p 16766:5432 -d postgres:latest
	sleep 10
	ENV_FOR_DYNACONF=testing pytest tests
	docker rm -f -v postgres_test
