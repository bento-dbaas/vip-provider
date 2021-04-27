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