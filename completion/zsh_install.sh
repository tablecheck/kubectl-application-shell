#!/bin/zsh

git clone https://github.com/tablecheck/kubectl-application-shell.git ~/.kubeas

mkdir -p ~/.oh-my-zsh/completions
chmod -R 755 ~/.oh-my-zsh/completions
ln -s ~/.kubeas/completion/kubectl-application-shell.zsh ~/.oh-my-zsh/completions/_kubeas.zsh
