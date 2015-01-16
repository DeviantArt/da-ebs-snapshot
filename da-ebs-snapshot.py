import sys
import os
import boto
import argparse


def parse_args:
    pass


def find_dependencies:
    pass


def connect_ec2:
    pass


def find_volume_id:
    pass


def lock_mysql:
    pass


def sync_fs:
    pass


def freeze_fs:
    pass


def snapshot:
    pass


def unfreeze_fs:
    pass


def unlock_mysql:
    pass


def declare_victory:
    pass


def main():
    steps = (parse_args,
             find_dependencies,
             connect_ec2,
             find_volume_id,
             lock_mysql,
             sync_fs,
             freeze_fs,
             snapshot,
             unfreeze_fs,
             unlock_mysql,
             declare_victory)

    config = None

    try:
        for step in steps:
            result = step(config)

            if config is None:
                config = result
    except Exception, e:
        print >> sys.stderr, "Error on step %s: %s %s" % (step.func_name, type(e), e)

        try:
            for hook in config.cleanup_hooks:
                hook()
        except AttributeError:
            pass
        except Exception, e:
            print >> sys.stderr, "Error in cleanup hook %s: %s %s" % (hook.func_name, type(e), e)
            print >> sys.stderr, "MySQL may still be locked and/or fs may still be frozen; MANUAL CLEANUP NECESSARY!"


if __name__ == __main__:
    sys.exit(main(sys.argv))
