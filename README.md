# snapshot_auto
Demo Project for AWS

## About

This project is a follow on from the Python beginners lecture. It uses boto3 to manage AWS EC2 instances.

## Configuring

shotty uses the configuration file created by the AWS CLI e.g.

'aws configure --profile shotty'

## Running

'pipenv run python shotty/shotty.py <command> <subcommand> <--project=PROJECT>'

*command* is instances, volumes, or snapshots
*subcommand* is list, start, stop, or snapshot depending on the command
*project* is optional
