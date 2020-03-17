# shellcheck disable=SC1008
#!/usr/local/bin/fish

git clone https://github.com/tablecheck/kubectl-application-shell.git ~/.kubeas

mkdir -p ~/.config/fish/completions
ln -s ~/kubeas/completion/kubeas.fish ~/.config/fish/completions/
