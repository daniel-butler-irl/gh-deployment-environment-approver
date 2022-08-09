import json
import os
import requests
import base64
import logging
from ruamel.yaml import YAML

from flask import Flask, request, jsonify
from github import GithubIntegration

app = Flask(__name__)
if os.environ.get('DEBUG', False):
    logging.basicConfig(level=logging.DEBUG)
    app.config['DEBUG'] = True
else:
    logging.basicConfig(level=logging.INFO)

app_id = os.getenv("APP_ID")
private_pem_encoded = os.getenv("PRIVATE_PEM_BASE_64")
approver_token = os.getenv("APPROVER_TOKEN")
allow_list_url = os.getenv("ALLOW_LIST_GIT_URL")

error = False
if app_id is None:
    app.logger.error("APP_ID Environment Variable Must be set")
    error = True
if private_pem_encoded is None:
    app.logger.error("PRIVATE_PEM_BASE_64 Environment Variable Must be set")
    error = True
if approver_token is None:
    app.logger.error("APPROVER_TOKEN Environment Variable Must be set")
    error = True
if allow_list_url is None:
    app.logger.error("ALLOW_LIST_GIT_URL Environment Variable Must be set.\n"
                     "Format: 'https://api.github.com/repos/{user}/{repo_name}/contents/{path_to_file}'")
    error = True

if error:
    exit(1)

app_key = base64.b64decode(private_pem_encoded).decode('ascii')
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
    app.logger.debug('Message Received')
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

        app.logger.debug("Requested")
        app.logger.debug(f"Environment: {environment}")
        app.logger.debug(f"Status: {status}")
        app.logger.debug(f"HTML URL: {html_url}")
        app.logger.debug(f"API URL: {repo_api_url}")
        app.logger.debug(f"Workflow Job Run ID: {wf_job_id}")
        app.logger.debug(f"Workflow Run ID: {wf_run_id}")
        app.logger.debug(f"Environment ID: {environment_id}")
        app.logger.debug(f"{owner} {repo_name}")

        # approval Can be one of: approved, rejected
        approval, reason = approval_check()

        response = handle_request(f'{repo_api_url}/actions/runs/{wf_run_id}/pending_deployments',
                                  approval,
                                  reason,
                                  [environment_id])

        app.logger.debug(f"Response: {response.json()}")

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
    app.logger.debug("Sending response to GitHub")
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

    app.logger.debug("Getting environment details....")
    response = requests.get(pending_url, headers=headers)
    app.logger.debug(response.json())
    for environment in response.json():
        if environment['environment']['name'] == environment_name:
            return environment['environment']['id']

    return None


def approval_check(user_to_check):
    app.logger.debug("Checking Approval")
    # approved or rejected are valid values
    approve = "rejected"
    reason = "Request not yet validated"

    allowed_teams, allowed_users = get_allow_lists()
    if allowed_teams is None and allowed_users is None:
        return approve, "No allow lists found"

    if allowed_teams:
        for team in allowed_teams:
            app.logger.debug(f"Checking if {user_to_check} is in {team} team")
            # TODO: Lookup team members
    if approve == "rejected" and allowed_users:
        for user in allowed_users:
            if user == user_to_check:
                app.logger.info(f"User {user} found in allow list")
                validate_user(user)
                break

    return approve, reason


def validate_user(user):
    validated = False
    app.logger.debug(f"Validate user {user}")
    # TODO: Preform additional validation checks (is the user who they say they are?)
    return validated


def get_allow_lists():
    req = requests.get(allow_list_url)
    if req.status_code == requests.codes.ok:
        req = req.json()  # the response is a JSON
        # req is now a dict with keys: name, encoding, url, size ...
        # and content. But it is encoded with base64.
        content = base64.decodestring(req['content'])
        yaml = YAML(typ='safe')
        allow_list = yaml.load(content)
        app.logger.debug(f"Allowed Teams: {allow_list['allow_teams']}")
        app.logger.debug(f"Allowed Users: {allow_list['allow_users']}")
        return allow_list['allow_teams'], allow_list['allow_users']
    else:
        app.logger.error('Allow list not found.')
        return None, None


if __name__ == "__main__":
    app.run(debug=True, port=5000)
