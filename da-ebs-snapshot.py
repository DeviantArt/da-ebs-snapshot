#!/usr/bin/env python

import sys
import os
import re
import uuid
import socket
import subprocess
import boto.ec2
import boto.utils
import argparse
import MySQLdb


def parse_args():
    parser = argparse.ArgumentParser(description='snapshot EBS volumes')

    parser.add_argument('mount_points', nargs='+', help='mount point of volume to snapshot')
    #parser.add_argument('-n', '--dry-run', action='store_true', help='help text')
    parser.add_argument('--access-key-id')
    parser.add_argument('--secret-access-key')
    parser.add_argument('-t', '--tag', dest='tags', action='append', metavar='NAME=VALUE')

    args = parser.parse_args()
    return args


def generate_uuid(config):
    config.tags.append("uuid=%s" % uuid.uuid4())


def find_dependencies(config):
    pass


def get_block_device(mount_point):
    print "searching for block device mounted at", mount_point

    mounts = {}
    with open('/proc/mounts', 'r') as proc_mounts:
        lines = proc_mounts.read().splitlines()
    for line in lines:
        columns = line.split(' ')
        mounts[columns[1]] = columns[0]
    return mounts[mount_point]


def get_region():
    print "determining region"

    availability_zone = boto.utils.get_instance_metadata()['placement']['availability-zone']
    region = re.sub('[a-z]+$', '', availability_zone)

    print "region is", region

    return region


def connect_ec2(config, region):
    print "connecting to EC2"

    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=config.access_key_id,
                                      aws_secret_access_key=config.secret_access_key)
    return conn


def normalize_bdev(bdev):
    return re.sub('^/dev/s', '/dev/xv', bdev)


def get_volume_id(conn, block_device):
    print "searching for EBS volume ID of", block_device

    instance_id = boto.utils.get_instance_metadata()['instance-id']
    volumes = conn.get_all_volumes(filters={
        'attachment.instance-id': instance_id})
    for volume in volumes:
        if normalize_bdev(volume.attach_data.device) == normalize_bdev(block_device):
            print "volume ID is", volume.id
            return volume.id

    raise Exception("EBS volume for %s not found!" % block_device)


def connect_mysql(config):
    print "connecting to MySQL"

    conn = MySQLdb.connect(read_default_file='/root/.my.cnf')
    return conn.cursor()


def lock_mysql(mysql):
    print "running FLUSH TABLES WITH READ LOCK"
    mysql.execute('FLUSH TABLES WITH READ LOCK')


def freeze_fs(mount_point):
    print "freezing filesystem mounted at", mount_point
    output = subprocess.check_output(['/sbin/fsfreeze', '-f', mount_point])
    if output:
        print 'fsfreeze -f output: %s' % output


def get_snapshot_description(mount_point):
    return "%s:%s" % (socket.getfqdn(), mount_point)


def create_snapshot(conn, volume_id):
    print "taking snapshot of %s" % volume_id
    snapshot = conn.create_snapshot(volume_id)
    print snapshot.id
    return snapshot


def tag_snapshot(snapshot, mount_point, additional_tags=[]):
    snapshot.add_tag('Name', get_snapshot_description(mount_point))

    for tag in additional_tags:
        name, value = tag.split('=', 1)
        snapshot.add_tag(name, value)


def unfreeze_fs(mount_point):
    print "unfreezing filesystem mounted at", mount_point
    output = subprocess.check_output(['/sbin/fsfreeze', '-u', mount_point])
    if output:
        print 'fsfreeze -u output: %s' % output


def unlock_mysql(mysql):
    print "running UNLOCK TABLES"
    mysql.execute('UNLOCK TABLES')


def declare_victory():
    print "VICTORY IS MINE"


def main():
    config = parse_args()
    generate_uuid(config)
    region = get_region()
    conn = connect_ec2(config, region)

    mysql = None

    try:
        block_devices = [get_block_device(mp) for mp in config.mount_points]
        volume_ids = [get_volume_id(conn, bdev) for bdev in block_devices]
        mysql = connect_mysql(config)
        lock_mysql(mysql)

        for mount_point in config.mount_points:
            freeze_fs(mount_point)

        for volume_id, mount_point in zip(volume_ids, config.mount_points):
            snapshot = create_snapshot(conn, volume_id)
            tag_snapshot(snapshot, mount_point, config.tags)
    except Exception, e:
        print "ERROR encountered: %s: %s" % (type(e), e)
        print "will attempt to unfreeze filesystem and unlock MySQL..."
    else:
        declare_victory()
    finally:
        for mount_point in reversed(config.mount_points):
            unfreeze_fs(mount_point)

        if mysql:
            unlock_mysql(mysql)


if __name__ == '__main__':
    sys.exit(main())
