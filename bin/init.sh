#!/bin/bash

shopt -s expand_aliases
umask 0022
alias vi="/usr/bin/vim"
alias ssh="ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no"
alias grep="/bin/grep --color"
alias modules="python /usr/local/p-tools/bin/modules.py"
alias ml="modules list"
alias mlip="modules listip"
alias mlmobile="modules listmobile"
alias mshow="modules show"
alias mr="modules rdepends"
alias ipconv="/usr/bin/perl /usr/local/p-tools/bin/ipconv.pl"
alias colordiff="/usr/bin/perl /usr/local/p-tools/bin/colordiff.pl"


_set_path() {
    local host=`hostname`
    (ml all op | fgrep -q "$host") && export PS1='\[\e]2;\u@\h\a\]\[\e[01;36m\]\u\[\e[01;35m\]@\[\e[01;33m\]\h\[\e[00m\]:\[\e[01;34m\]\w\$\[\e[00m\] ' && return
    (ml all single | fgrep -q "$host") && export PS1='\[\e]2;\u@\h\a\]\[\e[01;36m\]\u\[\e[01;35m\]@\[\e[01;31m\]\h\[\e[00m\]:\[\e[01;34m\]\w\$\[\e[00m\] ' && return
    export PS1='\[\e]2;\u@\h\a\]\[\e[01;36m\]\u\[\e[01;35m\]@\[\e[01;32m\]\h\[\e[00m\]:\[\e[01;34m\]\w\$\[\e[00m\] '
}

(echo "$-" | fgrep -q "i") && (echo "$TERM" | grep -qP '^(xterm|rxvt)') && _set_path
export EDITOR="/usr/bin/vim"

_color_echo() {
    tput setaf "$1"
    shift
    echo "$@"
    tput sgr0
}

opcd() {
    local date="`date +%Y%m%d`$1"
    mkdir -p "/data/opdir/$date" && cd "/data/opdir/$date"

opssh() {
    local ret
    if [[ $# -ne 2 ]]
    then
        echo "Usage: opssh host cmd" 1>&2
        return
    fi
    if [[ "$2" == "" ]]
    then
        ssh -qt "$1"
    else
        ssh -qt "$1" "source ~/.bashrc $2"
    fi
    ret=$?
    if [[ $ret -ne 0 ]]
    then
        _color_echo 2 "ssh $1 returned $ret" 1>&2
    fi
}

nsh() {
    if [ $# -eq 1 ]; then
        cat $1
    fi
    if [ $# -eq 2 ]; then
        cat $1 | pssh -i -t 0 -p 500 "$2"
    fi
}

ncp() {
    if [ $# -eq 3 ]; then
        cat $1 | prsync  -t 0 -p 500 "$2" "$3"
    fi
}

msh() {
    if [ $# -eq 1 ]; then
        ml all $1
    fi
    if [ $# -eq 2 ]; then
        ml all $1 | pssh -i -t 0 -p 500 "$2"
    fi
}

mcp() {
    if [ $# -eq 3 ]; then
        ml all $1 | prsync  -t 0 -p 500 "$2" "$3"
    fi
}

fsh() {
    local i
    if [[ $# -eq 1 || $# -eq 2 ]]
    then
        for i in $1; do _echo_host "$i" 1>&2; opssh "$i" "$2"; done
    elif [[ $# -eq 3 && "$2" == "read" ]]
    then
        for i in $1; do _echo_host "$i" 1>&2; read -p"Press ENTER to continue..."; opssh "$i" "$3"; done
    else
        echo "Usage:" 1>&2
        echo 'fsh "`ml pz edb`"' 1>&2
        echo 'fsh "`ml pz edb`" "df -h"' 1>&2
        echo 'fsh "`ml pz edb`" read "df -h"' 1>&2
    fi
}

fcp() {
    local i
    if [[ $# -ge 3 ]]
    then
        for i in $1; do _echo_host "$i" 1>&2; scp -r ${@:2:$(($#-2))} $i:${!#}; done
    else
        echo "Usage:" 1>&2
        echo 'fcp "`ml pz edb`" edb.conf edb/conf/' 1>&2
    fi
}

optail() {
    trap : SIGINT
    tail -F $@
    trap - SIGINT
}