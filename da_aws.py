import os
import sys
import re
import boto.ec2
import boto.utils


def get_region():
    availability_zone = boto.utils.get_instance_metadata()['placement']['availability-zone']
    region = re.sub('[a-z]+$', '', availability_zone)

    return region


def connect_ec2(access_key_id=None, secret_access_key=None, region=None):
    if region is None:
        region = get_region()

    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=access_key_id,
                                      aws_secret_access_key=secret_access_key)
    return conn


def get_my_volumes(conn):
    instance_id = boto.utils.get_instance_metadata()['instance-id']
    return conn.get_all_volumes(filters={'attachment.instance-id': instance_id})
