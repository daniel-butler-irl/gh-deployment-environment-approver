# gh-deployment-environment-approver
Approves environment deployment requests for allow listed users

The following environment variables need to be set

| Name | Description | 
| --- | --- |
| `APP_ID` |  Github Application ID |  
| `APPROVER_TOKEN` | GitHub Personal Access token for the approver user |  
| `PRIVATE_PEM_BASE_64` | Base64 encoded private key for the GitHub Application | 

