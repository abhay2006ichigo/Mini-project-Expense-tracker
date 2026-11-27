#!/bin/sh
set -eu

exec gosu app "$@"
