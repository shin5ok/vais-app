#!/bin/sh

TARGET=$1
if ! test -d $TARGET;
then
  echo "$TARGET looks like not directory"
  exit 1
fi

if ! ( pwd | grep devcontainer > /dev/null );
then
  echo "You must run in devcontainer, like './sync.sh ~/repos/your-repo-directory'"
  exit 2
fi

rsync -axv --delete --exclude '.git/' ./ $TARGET/.devcontainer/
