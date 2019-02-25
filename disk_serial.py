#!/usr/bin/env python3

"""
This is Linux specific, cumbersome and requires root. It would proably be better
to shell out to some utility::

    $ udevadm info --query=all --name=/dev/sda | grep -i serial
    E: ID_SERIAL=Samsung_SSD_840_EVO_120GB_S1D5NSBF476905T
    E: ID_SERIAL_SHORT=S1D5NSBF476905T

Or ever better - we have (optional) JSON output from 'lsblk'::

    $ lsblk --json --bytes --output-all --exclude 7,252
    ...
    {"name": "/dev/sda5", "fstype": "ext4", "label": null,
    "uuid": "8aec0077-f49c-4090-a132-e76d8df8221c", "mountpoint": "/"}
    ...

On Mac OS X::

    $ system_profiler SPHardwareDataType
    ...

"""

import sys, os, fcntl, struct

if os.geteuid() >  0:
    print("ERROR: Must be root to use")
    sys.exit(1)


print(sys.argv[1])

with open(sys.argv[1], "rb") as fd:
    # tediously derived from the monster struct defined in <hdreg.h>
    # see comment at end of file to verify
    hd_driveid_format_str = "@ 10H 20s 3H 8s 40s 2B H 2B H 4B 6H 2B I 36H I Q 152H"
    # Also from <hdreg.h>
    HDIO_GET_IDENTITY = 0x030d
    # How big a buffer do we need?
    sizeof_hd_driveid = struct.calcsize(hd_driveid_format_str)

    # ensure our format string is the correct size
    # 512 is extracted using sizeof(struct hd_id) in the c code
    assert sizeof_hd_driveid == 512

    # Call native function
    buf = fcntl.ioctl(fd, HDIO_GET_IDENTITY, " " * sizeof_hd_driveid)
    fields = struct.unpack(hd_driveid_format_str, buf)
    serial_no = fields[10].strip()
    model = fields[15].strip()
    print("Hard Disk Model: %s" % model)
    print("  Serial Number: %s" % serial_no)
