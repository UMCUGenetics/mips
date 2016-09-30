#!/usr/bin/env python
from __future__ import print_function

import sys
import os
import fnmatch
import subprocess

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 2:
        print("python mips_uuid_table.py /path/to/log/files_dir")
        sys.exit()

    log_dir = os.path.abspath(sys.argv[1])
    uuid_data = {}

    # Open log files and store in dict
    for log_file in os.listdir(log_dir):
        if log_file.endswith('.log'):
            log_file_path = '{0}/{1}'.format(log_dir,log_file)
            with open(log_file_path, 'r') as f:
                log_data = f.read().split('\n')[4:]
                for mip_data in log_data:
                    mip_data = mip_data.split('\t')
                    if len(mip_data) != 4:
                        continue
                    else:
                        uuids = mip_data[3].split(',')
                        for uuid in uuids:
                            if uuid != '':
                                if uuid not in uuid_data:
                                    uuid_data[uuid] = 1
                                else:
                                    uuid_data[uuid] += 1
    # Print results
    print("UUID\tUUID_Count")
    for uuid in uuid_data:
        print('{}\t{}'.format(uuid, uuid_data[uuid]))
    # ## Print log table to stdout
    # print('MIP_Name', end="\t")
    # for sample in samples:
    #     print('{0}-read_count\t{0}-dup_count'.format(sample), end="\t")
    # print(' ')
    #
    # for mip in mips_data.keys():
    #     print(mip, end="\t")
    #     for sample in samples:
    #         print('{0}\t{1}'.format(mips_data[mip][sample]['read_count'], mips_data[mip][sample]['dup_count']), end="\t")
    #     print(' ')
