.PHONY: prepare build build-generator build-test run run-generator test test-in-container clean send-master-sync send-pr-sync image-push deploy

IMAGE_NAME = quay.io/rhscl/betka
TEST_IMAGE_NAME = betka-test
DEPLOY_NAME = quay.io/rhscl/betka-deployment

# https://blog.153.io/2016/04/18/source-a-shell-script-in-make
-include secrets.mk
secrets.mk: secrets.env
	sed 's/"//g ; s/=/:=/' < $< > $@

prepare:
	mkdir -m 777 -p logs
	mkdir -m 777 -p betka-generator/results

build:
	docker-compose build betka

build-generator:
	docker-compose build generator

build-test: build
	docker build --tag ${TEST_IMAGE_NAME} -f Dockerfile.tests .

run: prepare build
	docker-compose up betka redis

run-generator: prepare build-generator
	docker-compose up generator

test:
	cd tests && PYTHONPATH=$(CURDIR) pytest --color=yes --verbose --showlocals

test-in-container: build-test
	docker run --rm --net=host -e DEPLOYMENT=test ${TEST_IMAGE_NAME}

image-push: build
	docker push ${IMAGE_NAME}

send-master-sync:
	docker-compose exec betka python3 /tmp/betka-bot/upstream_master_sync.py

clean:
	find . -name '*.pyc' -delete

stop:
	docker-compose down

image_deploy:
	docker build --tag=${DEPLOY_NAME} -f Dockerfile.deployment .

deploy: image_deploy
	./openshift/run-deployment-in-container.sh
