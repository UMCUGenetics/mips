#!/usr/bin/env python

import sys
import os
import fnmatch
import subprocess
import glob

def find_fastq(fastq_pattern, raw_data_dir):
    for file in os.listdir(raw_data_dir):
        if fnmatch.fnmatch(file, fastq_pattern):
            return os.path.abspath('{0}/{1}'.format(raw_data_dir, file))

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) != 6:
        print "python qsub_mips_trim_dedup.py /path/to/design.txt uuid_length uuid_read(R1,R2) /path/to/raw_data/sequencer/run/Data/Intensities/BaseCalls /path/to/output/folder"
        sys.exit()

    design_file = os.path.abspath(sys.argv[1])
    uuid_length = int(sys.argv[2])
    uuid_read = sys.argv[3]
    raw_data_dir = sys.argv[4]
    output_dir = sys.argv[5]

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
        log_file = "{0}/{1}.log".format(output_dir, sample)
        r1_fastq_paths = []
        r2_fastq_paths = []
        #find lanes
        for r1_fastq in glob.glob('{0}/{1}*R1_*.fastq.gz'.format(raw_data_dir,sample)):
            r1_fastq_paths.append(os.path.abspath(r1_fastq))
            r2_fastq_paths.append(os.path.abspath(r1_fastq).replace('_R1_','_R2_'))

        mips_trim_dedup_path = os.path.dirname(os.path.realpath(__file__))

        # Generate command and submit to cluster
        command = "python {0}/mips_trim_merge_dedup.py --design_file {1} --uuid_length {2} --uuid_read {3} -r1 {4} -r2 {5}".format(
            mips_trim_dedup_path,
            design_file,
            uuid_length,
            uuid_read,
            ' '.join(r1_fastq_paths),
            ' '.join(r2_fastq_paths))
        print command
        #subprocess.call("echo {0} | qsub -pe threaded 1 -l h_rt=1:0:0 -l h_vmem=2G -wd {1} -e {2} -o {2} -N {3}".format(command, output_dir, log_file, sample), shell=True)