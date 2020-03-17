#!/usr/local/bin/fish

git clone https://github.com/tablecheck/kubectl-application-shell.git ~/.kubeas

mkdir -p ~/.config/fish/completions
ln -s ~/.kubeas/completion/kubectl-application-shell.fish ~/.config/fish/completions/kubeas.fish
