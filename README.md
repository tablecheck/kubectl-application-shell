# kubectl-application-shell

### Description

This kubectl plugin allows you to solve this issue:

> You may want to run a one off sql query wrapped up in a script just to glean some information from the database. The traditional way to do this is by using `kubectl exec` into an existing pod running as part of your deployment. However, this may cause issues if your one-off command ends up killing the pod, which may impact production (dropping connections etc). It's much safer just to spin up a pod to do the one off task.

This command essentially wraps around `kubectl run`. It will allow you to specify a deployment name and the deployment namespace, and it will automatically grab the currently running image, resource limits/requests, config and secret mappings so that you have the required environment variables to complete your one-off task without impacting the existing deployment.

### Pre-requisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [jq](https://github.com/stedolan/jq/wiki/Installation)

### Installation

This uses pipenv in order to manage dependencies. You need Python 3.

### Usage

Run `pipenv install` and `pipenv shell`.

You can then run `kubeas` and it will give you the options.

It will automatically grab the image, resource limits/requests, config and secret mappings from the specified deployment.
