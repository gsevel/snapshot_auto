import boto3
import click
import botocore

session = boto3.Session(profile_name="shotty")
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []
    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()
    "Return instance iterator"
    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
def list_volumes(project):
    "List EBS Volumes attached to EC2 instances"
    instances = filter_instances(project)

    for i in instances:
        volumes = i.volumes.all()
        for v in volumes:
            tags = {t['Key']:t['Value'] for t in v.tags or []}
            print(", ".join((
                v.volume_id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted",
                tags.get('Project', '<no project>')
                )))
    return

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all of the snapshots, not just the most recent successful.")
def list_snapshots(project, list_all):
    "List EC2 Snapshots"
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                tags = {t['Key']:t['Value'] for t in s.tags or []}
                print(", ".join((
                    s.snapshot_id,
                    v.volume_id,
                    i.id,
                    s.description,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c"),
                    s.encrypted and "Encrypted" or "Not Encrypted",
                    tags.get('Project', '<no project>')
                    )))
                if s.state == "completed" and not list_all:
                    break
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshot',
    help="Create snapshots of all volumes")
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--verbose', 'verbose', default=False, is_flag=True,
    help="Print verbose output")
def snapshot_env(project, verbose):
    "Snapshot EC2 Instances"
    instances = filter_instances(project)

    for i in instances:
        print("Stopping instance {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Count not stop {0}. ".format(i.id) + str(e))
            continue
        i.wait_until_stopped()
        if verbose:
            print("\nInstance {0} is {1}".format(i.id,i.state['Name']),
                flush=True)
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("Snapshot of {0} already in progress, skipping.".format(
                    v.volume_id
                    ))
            else:
                print("Creating snapshot of {0}".format(v.volume_id))
                response = v.create_snapshot(Description="Created by AutoShotty")
        i.start()
        i.wait_until_running()

    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
def list_env(project):
    "List EC2 Instances"
    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']:t['Value'] for t in i.tags or []}
        print(", ".join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))
    return

@instances.command('stop')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
def stop_instances(project):
    "Stop EC2 Instances"

    "filter instances by project if supplied"
    instances = filter_instances(project)
    "Iterate through instances and stop, printing their ID."
    for i in instances:
        print("Stopping instance {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Count not stop {0}. ".format(i.id) + str(e))
            continue
    return

@instances.command('start')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
def start_instances(project):
    "Start EC2 Instances"

    "filter instances by project if supplied"
    instances = filter_instances(project)
    "Iterate through instances and start, printing their ID."
    for i in instances:
        print("Starting instance {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Count not start {0}. ".format(i.id) + str(e))
            continue
    return

if __name__ == '__main__':
    cli()
