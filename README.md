DeviantArt EBS utilities
========================

da-ebs-snapshot
---------------

This utility creates a consistent snapshot of one or more local filesystems.  Given one or more mount points, it determines EBS volume IDs, freezes tables in MySQL, freezes the filesystems, and snapshots them.  It tags snapshots taken together with an identical `uuid` tag.

da-prune-snapshots
------------------

This utility prunes snapshots of volumes attached to the current instance.  It uses the `ttl` tag on the snapshot to determine whether it has expired and should be deleted.  When using `da-ebs-snapshot`, add a `--tag ttl=86400` tag to schedule the snapshot(s) for deletion after 1 day.  For x hours/x days/x weeks/x months snapshot retention schemes, use multiple cron jobs run hourly, daily, weekly, etc, each with a different TTL.

library
-------

Included is `da_aws.py`, a couple of common utility functions used by the scripts.  These are installed in `/usr/local/lib/python` by the debian package.  To easily add this path to your PYTHONPATH globally, add a file `/usr/local/lib/python<version>/dist-packages/local.pth` containing `/usr/local/lib/python`.
