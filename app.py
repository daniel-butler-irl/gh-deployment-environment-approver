import json
import os
import requests
import base64

from flask import Flask, request
from github import GithubIntegration


app = Flask(__name__)
app_id = os.getenv("APP_ID")
# Read the bot certificate
app_key = base64.b64decode(os.getenv("PRIVATE_PEM_BASE_64")).decode('ascii')
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


@app.route("/", methods=['POST'])
def bot():
    # Get the event payload
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

        print("Requested")
        print(f"Environment: {environment}")
        print(f"Status: {status}")
        print(f"HTML URL: {html_url}")
        print(f"API URL: {repo_api_url}")
        print(f"Workflow Job Run ID: {wf_job_id}")
        print(f"Workflow Run ID: {wf_run_id}")
        print(f"Environment ID: {environment_id}")
        print(f"{owner} {repo_name}")

        # approval Can be one of: approved, rejected
        approval = "rejected"
        print(isinstance(environment_id, int))
        handle_request(f'{repo_api_url}/actions/runs/{wf_run_id}/pending_deployments',
                       approval,
                       "Rejection test",
                       [environment_id])

    elif action == 'approved':
        print("Approved")
        print(f"Approver: {payload['approver']['login']}")
        print(f"Comment: {payload['comment']}")
    elif action == 'rejected':
        print("Rejected")
        print(f"Approver: {payload['approver']['login']}")
        print(f"Comment: {payload['comment']}")
    else:
        print('Unknown action')
        print(f"{json.dumps(payload, indent=4, sort_keys=True)}")

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

    response = requests.post(pending_url, headers=headers, data=json.dumps(body))
    print(f"Send: {response.request.body}")
    print(f"Response: {response.json()}")


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

    print("Getting environment details....")
    response = requests.get(pending_url, headers=headers)
    print(response.json())
    for environment in response.json():
        if environment['environment']['name'] == environment_name:
            return environment['environment']['id']

    return None


if __name__ == "__main__":
    app.run(debug=True, port=3000)
