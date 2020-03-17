git clone https://github.com/tablecheck/kubectl-application-shell.git ~/.kubeas

COMPDIR=$(pkg-config --variable=completionsdir bash-completion)
ln -sf ~/.kubeas/completion/kubectl-application-shell.bash $COMPDIR/kubeas
cat << FOE >> ~/.bashrc


#kubeas
export PATH=~/.kubeas:\$PATH
FOE
