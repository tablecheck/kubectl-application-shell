complete -f -c kubeas -n '__fish_contains_opt name' -a "(kubectl get deployments -o=name)" 
complete -f -c kubeas -n '__fish_contains_opt namespace' -a "(kubectl get namespaces -o=name)"
