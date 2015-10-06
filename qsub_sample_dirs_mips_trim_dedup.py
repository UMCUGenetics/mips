#!/usr/bin/env python

import sys
import os
import fnmatch
import subprocess

def find_fastq(fastq_pattern, sample_dir):
    for file in os.listdir(sample_dir):
        if fnmatch.fnmatch(file, fastq_pattern):
            return os.path.abspath('{0}/{1}'.format(sample_dir, file))

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 4:
        print "python qsub_mips_trim_dedup.py /path/to/design.txt /path/to/raw_data/sequencer/run/Unaligned/project /path/to/output/folder"
        sys.exit()

    design_file = os.path.abspath(sys.argv[1])
    raw_data_dir = sys.argv[2]
    output_dir = sys.argv[3]

    if not os.path.exists(output_dir):
	os.makedirs(output_dir)

    # Trim and dedup per sample
    for sample_dir in os.listdir(raw_data_dir):
        sample_dir_path = raw_data_dir + "/" + sample_dir
        sample_log_path = "{0}/{1}.log".format(output_dir, sample_dir)
        r1_fastq = find_fastq('*_R1_*.fastq.gz',sample_dir_path)
        r2_fastq = find_fastq('*_R2_*.fastq.gz',sample_dir_path)

        mips_trim_dedup_path = os.path.dirname(os.path.realpath(__file__))

        # Generate command and submit to cluster
        command = "python {0}/mips_trim_dedup.py {1} {2} {3}".format(mips_trim_dedup_path, design_file, r1_fastq, r2_fastq)
        subprocess.call("echo {0} | qsub -pe threaded 1 -q veryshort -wd {1} -e {2} -o {2}".format(command, output_dir, sample_log_path), shell=True)
