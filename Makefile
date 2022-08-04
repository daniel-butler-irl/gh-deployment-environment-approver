IMAGE=gh-deployment-approver
REGISTRY=us.icr.io/dev-containers/${IMAGE}

local-setup:
	npm install --global smee-client
	pip install -r requirements.txt

build:
#   I am building on an M1 Mac this builds for the platform code engine expects
	docker buildx build --platform linux/amd64 --tag ${IMAGE} .

publish:
	docker tag ${IMAGE} ${REGISTRY}
	docker push ${REGISTRY}
