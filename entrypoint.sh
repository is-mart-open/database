#!/bin/bash

set -e

# load environmental variable, info from: https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env

# make cronjob run, info from: https://stackoverflow.com/questions/37458287/how-to-run-a-cron-job-inside-a-docker-container
# run cron at foreground(for docker)
cron -f
