#!/bin/bash

export PYTHONPATH=".:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="test_settings"

PROG="$0"
CMD="$1"
shift

usage() {
    echo "USAGE: $PROG [command]"
    echo "  test - run the jsonview tests"
    echo "  shell - open the Django shell"
    exit 1
}

case "$CMD" in
    "test" )
        django-admin.py test jsonview $@ ;;
    "shell" )
        django-admin.py shell $@ ;;
    * )
        usage ;;
esac
