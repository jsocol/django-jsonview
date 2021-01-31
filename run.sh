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
        echo "Django version: $(python -m django --version)"
        python -m django test jsonview "$@"
        ;;
    "shell" )
        python -m django shell "$@"
        ;;
    "check" )
        echo "Flake8 version: $(flake8 --version)"
        flake8 jsonview "$@"
        ;;
    "coverage" )
        echo "Django version: $(python -m django --version)"
        coverage3 run -m django test jsonview "$@"
        coverage3 report \
            -m \
            --include=jsonview/* \
            --omit=jsonview/tests.py \
            --fail-under=100
        ;;
    * )
        usage ;;
esac
