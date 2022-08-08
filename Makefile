IMAGE=gh-deployment-approver
REGISTRY=us.icr.io/dev-containers/${IMAGE}

ifndef BUILD_DATE
  override BUILD_DATE:=$(shell /bin/date "+%Y%m%d-%H%M%S")
endif

local-setup:
	npm install --global smee-client
	pip install -r requirements.txt

build:
#   I am building on an M1 Mac this builds for the platform code engine expects
	docker buildx build --platform linux/amd64 --tag ${IMAGE} -f oci/Dockerfile .

publish:
	docker tag ${IMAGE} ${REGISTRY}:latest
	docker tag ${IMAGE} ${REGISTRY}:${BUILD_DATE}
	docker push ${REGISTRY}:latest
	docker push ${REGISTRY}:${BUILD_DATE}
