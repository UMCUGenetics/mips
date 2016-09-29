#!/usr/bin/env python
from __future__ import print_function

import sys
import os
import fnmatch
import subprocess

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 2:
        print("python mips_log_table.py /path/to/log/files_dir")
        sys.exit()

    log_dir = os.path.abspath(sys.argv[1])
    mips_data = {}
    samples = []

    # Open log files and store in dict
    for log_file in os.listdir(log_dir):
        if log_file.endswith('.log'):
            log_file_path = '{0}/{1}'.format(log_dir,log_file)
            sample = log_file[:-4]
            samples.append(sample)
            with open(log_file_path, 'r') as f:
                log_data = f.read().split('\n')[4:]
                for mip_data in log_data:
                    mip_data = mip_data.split('\t')
                    if len(mip_data) != 3:
                        continue
                    else:
                        mip_name = mip_data[0]
                        read_count = mip_data[1]
                        dup_count = mip_data[2]
                        if mip_name not in mips_data.keys():
                            mips_data[mip_name] = {}
                        mips_data[mip_name][sample] = {'read_count':read_count,'dup_count':dup_count}

    ## Print log table to stdout
    print('MIP_Name', end="\t")
    for sample in samples:
        print('{0}-read_count\t{0}-dup_count'.format(sample), end="\t")
    print(' ')

    for mip in mips_data.keys():
        print(mip, end="\t")
        for sample in samples:
            print('{0}\t{1}'.format(mips_data[mip][sample]['read_count'], mips_data[mip][sample]['dup_count']), end="\t")
        print(' ')
