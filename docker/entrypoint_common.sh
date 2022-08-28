#!/bin/bash

# set HOME explicitly
export HOME=/home/ops

# get group id
GID=$(id -g)

# temporarily change home dir to bypass usermod's recursive chown of home dir
gosu 0:0 usermod -d /tmp/${HOME} ops 2>/dev/null

# update user and group ids
gosu 0:0 groupmod -g $GID ops 2>/dev/null
gosu 0:0 usermod -u $UID -g $GID ops 2>/dev/null
gosu 0:0 usermod -aG docker ops 2>/dev/null

# restore home dir
gosu 0:0 usermod -d ${HOME} ops 2>/dev/null

# update ownership of home dir and hidden files/dirs
gosu 0:0 chown $UID:$GID $HOME 2>/dev/null || true
gosu 0:0 chown -R $UID:$GID $HOME/.[!.]* 2>/dev/null || true

# update ownership of verdi files/dirs
gosu 0:0 chown $UID:$GID $HOME/verdi 2>/dev/null || true
gosu 0:0 chown $UID:$GID $HOME/verdi/ops 2>/dev/null || true
gosu 0:0 chown -R $UID:$GID $HOME/verdi/etc 2>/dev/null || true
gosu 0:0 chown -R $UID:$GID $HOME/verdi/log 2>/dev/null || true
gosu 0:0 chown -R $UID:$GID $HOME/verdi/run 2>/dev/null || true

# update ownership of other files
gosu 0:0 chown -R $UID:$GID /var/run/docker.sock 2>/dev/null || true
