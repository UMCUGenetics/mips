#!/usr/bin/env python

import sys
import os
import fnmatch
import subprocess
import glob

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 4:
        print "python qsub_mips_trim_dedup.py /path/to/design.txt /path/to/raw_data/sequencer/run/Unaligned/project /path/to/output/folder"
        sys.exit()

    design_file = os.path.abspath(sys.argv[1])
    raw_data_dir = sys.argv[2]
    output_dir = sys.argv[3]

    mips_trim_dedup_path = os.path.dirname(os.path.realpath(__file__))

    if not os.path.exists(output_dir):
	os.makedirs(output_dir)

    # Trim and dedup per sample
    for sample_dir in os.listdir(raw_data_dir):
        sample_dir_path = raw_data_dir + "/" + sample_dir
        
        # Per lane
        for r1_fastq in glob.glob('{0}/*R1_*.fastq.gz'.format(sample_dir_path)):
	    r1_fastq_path = os.path.abspath(r1_fastq)
	    r2_fastq_path = r1_fastq_path.replace('_R1_','_R2_')
	    lane = r1_fastq_path.split('_')[-3]
	    sample_lane = "{0}_{1}".format(sample_dir, lane)
	    log_file = "{0}/{1}.log".format(output_dir, sample_lane)

	    # Generate command and submit to cluster
	    command = "python {0}/mips_trim_dedup.py {1} {2} {3}".format(mips_trim_dedup_path, design_file, r1_fastq_path, r2_fastq_path)
	    subprocess.call("echo {0} | qsub -pe threaded 1 -l h_rt=1:0:0 -l h_vmem=2G -wd {1} -e {2} -o {2} -N {3}".format(command, output_dir, log_file, sample_lane), shell=True)
