#!/bin/sh
set -eu

usage() {

  cat << EOF
Template script for replacing occurances of @@MYPROJECT@@ and @@MYORG@@ with
desired strings.

Deletes itself on a successful run.

usage:

    GITHUB_PROJECT_NAME=foo GITHUB_ORG_NAME=baz $0

EOF
  return 1
}

GITHUB_PROJECT_NAME="${GITHUB_PROJECT_NAME:-}"
GITHUB_ORG_NAME="${GITHUB_ORG_NAME:-}"
help="${1:-}"

if [ -n "${help}" ]; then
  usage
  exit 2
fi

if [ -z "${GITHUB_PROJECT_NAME}" ] || [ -z "${GITHUB_ORG_NAME}" ]; then
  echo >&2 "Missing GITHUB_PROJECT_NAME or GITHUB_ORG_NAME in environment."
  exit 1
fi

if ! git status -s >/dev/null 2>&1; then
  echo >&2 "Uncommitted changes detected, exiting."
  exit 1
fi


find . \( -type d -name .git -prune \) -o -type f -print0 | LC_ALL=C xargs -0 sed -i '' 's/@@MYPROJECT@@/'"$GITHUB_PROJECT_NAME"'/'

find . \( -type d -name .git -prune \) -o -type f -print0 | LC_ALL=C xargs -0 sed -i '' 's/@@MYORG@@/'"$GITHUB_ORG_NAME"'/'

github_project_name_lc=$(echo "$GITHUB_PROJECT_NAME" | tr '[:upper:]' '[:lower:]')
mv myapp.spec "${github_project_name_lc}.spec"
mv myapp "${GITHUB_PROJECT_NAME}"

echo "Finished renaming template; removing $0"
rm -f "$0" && git rm "$0"
