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
    echo "  check - run flake8"
    echo "  coverage - run tests with coverage"
    exit 1
}

case "$CMD" in
    "test" )
        django-admin.py test jsonview $@
        ;;
    "shell" )
        django-admin.py shell $@
        ;;
    "check" )
        flake8 jsonview $@
        ;;
    "coverage" )
        coverage run `which django-admin.py` test jsonview $@
        coverage report \
            -m \
            --include=jsonview/* \
            --omit=jsonview/tests.py \
            --fail-under=100
        ;;
    * )
        usage ;;
esac
