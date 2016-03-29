#!/usr/bin/env python

import sys
import os
import fnmatch
import subprocess

def find_fastq(fastq_pattern, raw_data_dir):
    for file in os.listdir(raw_data_dir):
        if fnmatch.fnmatch(file, fastq_pattern):
            return os.path.abspath('{0}/{1}'.format(raw_data_dir, file))

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 4:
        print "python qsub_mips_trim_dedup.py /path/to/design.txt /path/to/raw_data/sequencer/run/Data/Intensities/BaseCalls /path/to/output/folder"
        sys.exit()

    design_file = os.path.abspath(sys.argv[1])
    raw_data_dir = sys.argv[2]
    output_dir = sys.argv[3]

    if not os.path.exists(output_dir):
	os.makedirs(output_dir)

    # Find all samples in raw data dir
    samples = set([])
    for file in os.listdir(raw_data_dir):
	if file.endswith(".fastq.gz"):
	    sample = file.split('_')[0]
	    samples.add(sample)

    # Trim and dedup per sample
    for sample in samples:
	sample_log_path = "{0}/{1}.log".format(output_dir, sample)
	r1_fastq = find_fastq("{0}*_R1_*.fastq.gz".format(sample),raw_data_dir)
	r2_fastq = find_fastq("{0}*_R2_*.fastq.gz".format(sample),raw_data_dir)
	
	mips_trim_dedup_path = os.path.dirname(os.path.realpath(__file__))
	
	# Generate command and submit to cluster
        command = "python {0}/mips_trim_dedup.py {1} {2} {3}".format(mips_trim_dedup_path, design_file, r1_fastq, r2_fastq)
        subprocess.call("echo {0} | qsub -pe threaded 1 -l h_rt=1:0:0 -l h_vmem=2G -wd {1} -e {2} -o {2}".format(command, output_dir, sample_log_path), shell=True)
