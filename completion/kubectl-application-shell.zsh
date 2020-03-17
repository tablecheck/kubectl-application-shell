#compdef kubeas

local all_namespaces="$(kubectl get namespaces -o=name)"
local deployments="$(kubectl get deployments --all-namespaces -o=name)"
_arguments \
  "--name:*: :(${deployments})" \
  "--namespace:*: :(${all_namespaces})" \
