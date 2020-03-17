# kubectl-application-shell


### Description

This kubectl plugin allows you to solve this issue:

> You may want to run a one off sql query wrapped up in a script just to glean some information from the database. The traditional way to do this is by using `kubectl exec` into an existing pod running as part of your deployment. However, this may cause issues if your one-off command ends up killing the pod, which may impact production (dropping connections etc). `kubectl run` is perfect for this since we don't want. It's much safer just to spin up a pod to do the one off task.

This command will allow you to specify a deployment name and the deployment namespace, and it will automatically grab the currently running image, config and secret mappings so that you have the required environment variables to complete your task.

### Installation

To install it, add `src/kubectl-application-shell` to your PATH.

### Usage

Example: `kubectl application shell --name my-deployment-name --namespace my-namespace`

```
*  --namespace Deployment Namespace
*  --name Deployment Name
   --image Container Image
   --config Container Config Map name
   --secret Container Config Secret name
```
`*` = Required

It will automatically grab the image, config and secret from the existing deployment name.
