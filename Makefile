dev:
	export FLASK_DEBUG=1

run:
	export FLASK_APP=./vip_provider/app.py; export FLASK_DEBUG=1; python -m flask run --host 0.0.0.0 --port=5001

deploy_dev:
	tsuru app-deploy -a vip-provider-dev .

deploy_prod:
	tsuru app-deploy -a vip-provider .

test:
	export DBAAS_HTTP_PROXY=; export DBAAS_HTTPS_PROXY=;coverage run --source=./ -m unittest discover --start-directory ./vip_provider/tests -p "*.py"

test_report: test
	coverage report -m



# Docker part, for deploy
# TODO, standardize with other providers

docker_build:
	GIT_BRANCH=$$(git branch --show-current); \
	GIT_COMMIT=$$(git rev-parse --short HEAD); \
	DATE=$$(date +"%Y-%M-%d_%T"); \
	INFO="date:$$DATE  branch:$$GIT_BRANCH  commit:$$GIT_COMMIT"; \
	docker build -t dbaas/vip_provider --label git-commit=$(git rev-parse --short HEAD) --build-arg build_info="$$INFO" .

docker_run:
	make docker_stop
	docker rm vip_provider || true
	docker run --name=vip_provider -d -p 8000:80 --platform linux/amd64 --env "WORKERS=2" --env "PORT=80" dbaas/vip_provider 

docker_stop:
	docker stop vip_provider || true

docker_deploy_gcp:
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso:"
	@echo "make docker_deploy_gcp TAG=v1.02"
	@echo "Checar as tags atuais: https://console.cloud.google.com/artifacts/docker/gglobo-dbaas-hub/us-east1/dbaas-docker-images?project=gglobo-dbaas-hub"
	make docker_deploy_build TAG=${TAG}
	make docker_deploy_push TAG=${TAG}

docker_deploy_build: 
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_build TAG=v1.02"
	GIT_BRANCH=$$(git branch --show-current); \
	GIT_COMMIT=$$(git rev-parse --short HEAD); \
	DATE=$$(date +"%Y-%M-%d_%T"); \
	INFO="date:$$DATE  branch:$$GIT_BRANCH  commit:$$GIT_COMMIT"; \
	docker build . -t us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/vip-provider:${TAG} \
		--label git-commit=$(git rev-parse --short HEAD) \
		--build-arg build_info="$$INFO"

docker_deploy_push:
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_push TAG=v1.02"
	docker push us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/vip-provider:${TAG}