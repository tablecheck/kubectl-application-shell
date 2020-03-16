# kubectl-application-shell

This kubectl plugin allows you to solve this issue:
```
The applications tend to be monolithic and require the entire codebase to be baked into the image. The codebase contains methods and scripts related to the application usually for interacting with persistent storage (database, elasticsearch, etc.). The code itself relies on environment variables that it uses as parameters to connect to the persistent storage.

For example someone many want to run a one off sql query wrapped up in a script just to glean some information from the database. run is perfect for this since we don't want to disrupt existing workers and prefer to spin up a one off pod to do this query which outputs to the users terminal. Pairing this with --env-from makes it easy just to hook into the configmap and secretsmaps which already contain the variables necessary to make the connection to the persistent storage.

We could simply exec into a pod that's part of a deployment and has all the environment variables already after orphaning it but we also don't want to endanger any work that pod is currently doing. Part of the problem is the nature of the work itself. It's much safer just to spin up a pod to do the one off task.
```

To install it, add `src/kubectl-application-shell` to your PATH.

Usage:

```
*  --namespace Deployment Namespace
*  --name Deployment Name
   --image Container Image
   --config Container Config Map name
   --secret Container Config Secret name
```
`*` = Required

It will automatically grab the image, config and secret from the existing deployment name.
