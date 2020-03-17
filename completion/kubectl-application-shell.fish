complete -f -c kubeas -n '__fish_contains_opt name' -a "(kubectl get deployments -ocustom-columns=":.metadata.name")" 
complete -f -c kubeas -n '__fish_contains_opt namespace; and not __fish_contains_opt name' -a "(kubectl get namespaces -ocustom-columns=":.metadata.name")"
