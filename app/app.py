import json
import os
import requests
import base64

from flask import Flask, request, jsonify
from github import GithubIntegration


app = Flask(__name__)
app.config['DEBUG'] = True

app_id = os.getenv("APP_ID")
error = False
if app_id is None:
    app.logger.error("APP_ID Environment Variable Must be set")
    error = True
if os.getenv("PRIVATE_PEM_BASE_64") is None:
    app.logger.error("PRIVATE_PEM_BASE_64 Environment Variable Must be set")
    error = True
if os.getenv("APPROVER_TOKEN") is None:
    app.logger.error("APPROVER_TOKEN Environment Variable Must be set")
    error = True
if error:
    exit(1)

app_key = base64.b64decode(os.getenv("PRIVATE_PEM_BASE_64")).decode('ascii')
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


@app.route('/debug', methods=['GET'])
def default_route():
    """Default route"""
    app.logger.debug('this is a DEBUG message')
    app.logger.info('this is an INFO message')
    app.logger.warning('this is a WARNING message')
    app.logger.error('this is an ERROR message')
    app.logger.critical('this is a CRITICAL message')
    return jsonify('hello world')


@app.route("/", methods=['POST'])
def bot():
    # Get the event payload
    app.logger.info('Message Received')
    payload = request.json
    # print(f"{json.dumps(payload, indent=4, sort_keys=True)}")
    action = payload['action']
    if action == 'requested':

        environment = payload['environment']

        wf_job_run = payload['workflow_job_run']
        status = wf_job_run['status']
        html_url = wf_job_run['html_url']
        owner = payload['repository']['owner']['login']
        repo_name = payload['repository']['name']
        repo_api_url = payload['repository']['url']
        wf_run_id = payload["workflow_run"]["id"]
        wf_job_id = wf_job_run["id"]
        pending_deployments_api = f'{repo_api_url}/actions/runs/{wf_run_id}/pending_deployments'
        environment_id = get_environment_id(pending_deployments_api, owner, repo_name, environment)

        app.logger.info("Requested")
        app.logger.info(f"Environment: {environment}")
        app.logger.info(f"Status: {status}")
        app.logger.info(f"HTML URL: {html_url}")
        app.logger.info(f"API URL: {repo_api_url}")
        app.logger.info(f"Workflow Job Run ID: {wf_job_id}")
        app.logger.info(f"Workflow Run ID: {wf_run_id}")
        app.logger.info(f"Environment ID: {environment_id}")
        app.logger.info(f"{owner} {repo_name}")

        # approval Can be one of: approved, rejected
        approval, reason = approval_check()

        handle_request(f'{repo_api_url}/actions/runs/{wf_run_id}/pending_deployments',
                       approval,
                       reason,
                       [environment_id])

    elif action == 'approved':
        app.logger.info("Approved")
        app.logger.info(f"Approver: {payload['approver']['login']}")
        app.logger.info(f"Comment: {payload['comment']}")
    elif action == 'rejected':
        app.logger.info("Rejected")
        app.logger.info(f"Approver: {payload['approver']['login']}")
        app.logger.info(f"Comment: {payload['comment']}")
    else:
        app.logger.info('Unknown action')
        app.logger.info(f"{json.dumps(payload, indent=4, sort_keys=True)}")

    return "ok"


def handle_request(pending_url, approval, comment, environment_ids):

    headers = {
        'Accept': 'application/vnd.github+json-H',
        'Authorization': f'token {os.getenv("APPROVER_TOKEN")}',
    }
    body = {
        'environment_ids': environment_ids,
        'state': f'{approval}',
        'comment': f'{comment}'
    }

    return requests.post(pending_url, headers=headers, data=json.dumps(body))


def get_environment_id(pending_url, owner, repo_name, environment_name):
    # Here is where we are getting the permission to talk as our bot and not
    # as a Python webservice
    token = git_integration.get_access_token(
        git_integration.get_installation(owner, repo_name).id
    ).token

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'token {token}',
    }

    app.logger.info("Getting environment details....")
    response = requests.get(pending_url, headers=headers)
    app.logger.info(response.json())
    for environment in response.json():
        if environment['environment']['name'] == environment_name:
            return environment['environment']['id']

    return None


def approval_check():
    approve = False
    reason = "Request not yet validated"

    return approve, reason


if __name__ == "__main__":
    app.run(debug=True, port=5000)
