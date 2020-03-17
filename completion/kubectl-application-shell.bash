_kube_contexts()
{
  local curr_arg;
  curr_arg=${COMP_WORDS[COMP_CWORD]}
  COMPREPLY=( $(compgen -W "- $(kubectl get deployments --all-namespaces -o=name)" -- $curr_arg ) );
}

complete -F _kube_contexts kubeas
