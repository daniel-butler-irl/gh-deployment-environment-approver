local-setup:
	npm install --global smee-client
	pip install -r requirements.txt

build:
	docker build --tag gh-deployment-approver .
