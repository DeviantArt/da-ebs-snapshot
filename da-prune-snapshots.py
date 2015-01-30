#!/usr/bin/env python


"""Very simple script to prune old EBS snapshots.  It looks for all snapshots
of volumes attached to the local machine.  It looks for the 'ttl' tag, and
deletes a snapshot if its ttl (in seconds) has elapsed."""


import os
import sys
import argparse
from dateutil.parser import parse as parse_datetime
import dateutil.tz

from datetime import datetime, timedelta
import boto.ec2
import boto.utils

from da_aws import connect_ec2, get_my_volumes


UTC = dateutil.tz.tzutc()


def parse_args():
    parser = argparse.ArgumentParser(description='clean up old EBS snapshots')

    parser.add_argument('--access-key-id')
    parser.add_argument('--secret-access-key')

    args = parser.parse_args()
    return args


def main():
    config = parse_args()
    conn = connect_ec2(config.access_key_id, config.secret_access_key)

    volumes = [v.id for v in get_my_volumes(conn)]
    snapshots = conn.get_all_snapshots(filters={'volume-id': volumes})

    # Someone please explain to me why utcnow() produces a timezone-naive
    # datetime.
    now = datetime.utcnow().replace(tzinfo=UTC)

    for snapshot in snapshots:
        if 'ttl' in snapshot.tags:
            try:
                ttl = int(snapshot.tags['ttl'])
            except ValueError:
                continue

            print "considering", snapshot.id

            cutoff = parse_datetime(snapshot.start_time) + timedelta(seconds=ttl)

            if now > cutoff:
                print "deleting", snapshot.id
                snapshot.delete()


if __name__ == '__main__':
    sys.exit(main())
