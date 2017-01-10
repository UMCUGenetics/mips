#!/usr/bin/env python


import sys
import re
import argparse
from itertools import izip_longest, izip
import gzip
import contextlib


def reverse_complement(seq):
    """
    Return reverse complement of a dna sequence.
    """
    bases_dict = {
        'A': 'T', 'a': 't',
        'C': 'G', 'g': 'c',
        'G': 'C', 'c': 'g',
        'T': 'A', 't': 'a'}
    return "".join([bases_dict[base] for base in reversed(seq)])


def parse_design(design_file):
    """
    Parse design file and return mips dictonary.
    """
    mips = {}
    with open(design_file, 'r') as f:
        header = f.readline().strip('\n').split('\t')

        # Check header
        if header[6] != 'ext_probe_sequence':
            print "Error: column 7 in design file should be: ext_probe_sequence"
            sys.exit()
        elif header[10] != 'lig_probe_sequence':
            print "Error: column 11 in design file should be: lig_probe_sequence"
            sys.exit()
        elif header[19] != 'mip_name':
            print "Error: column 20 in design file should be: mip_name"
            sys.exit()

        # Parse MIPS
        for line in f:
            line = line.strip('\n').split('\t')

            mip_name = line[19]
            ext_probe = line[6]
            ext_probe_revcom = reverse_complement(ext_probe)
            lig_probe = line[10]
            lig_probe_revcom = reverse_complement(lig_probe)

            mips[mip_name] = {
                'ext_probe': ext_probe, 'ext_probe_revcom': ext_probe_revcom,
                'lig_probe': lig_probe, 'lig_probe_revcom': lig_probe_revcom,
                'uuids': set({}),
                'count': 0, 'dup_count': 0
            }

    return mips


def grouper(iterable, n, fillvalue=None):
    """Helper function to read in fasta file per 4 lines."""
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


class FixedGzip(gzip.GzipFile):
    """Fix gzip class to work with contextlib.nested in python 2.6."""

    def __enter__(self):
        if self.fileobj is None:
            raise ValueError("I/O operation on closed GzipFile object")
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=200),
    description = 'Trim, merge and dedup fastq files from mips experiment. Assumes fastq naming convention: sample_flowcell_index_lane_R[12]_tag.fastq.gz and fastq files from one sample.')
    parser.add_argument('-d', '--design_file', type=str, help='Mips design file', required=True)
    parser.add_argument('-r1', '--r1_fastq', type=str, help='R1 fastq', required=True, nargs='*')
    parser.add_argument('-r2', '--r2_fastq', type=str, help='R2 fastq', required=True, nargs='*')
    parser.add_argument('-l',' --uuid_length', type=int, help='UUID length', required=True)
    parser.add_argument('-ur', '--uuid_read', type=str, help='Read containing UUID', choices=['R1', 'R2'], required=True)
    args = parser.parse_args()

    # Check input fastq's
    if len(args.r1_fastq) != len(args.r2_fastq):
        parser.error("Arguments -r1/--r1_fastq and -r2/--r2_fastq should be of equal length.")

    mips = parse_design(args.design_file)
    unique_uuids = set({})

    # Output files
    fastq_1_file_out = "trimmed-dedup-"+args.r1_fastq[0].split('/')[-1]
    fastq_2_file_out = "trimmed-dedup-"+args.r2_fastq[0].split('/')[-1]
    if len(args.r1_fastq) > 1 and len(args.r2_fastq) > 1:  # Multiple fastq's -> merge
        fastq_1_file_out = re.sub('_L\d{3}_', '_LMerged_', fastq_1_file_out)
        fastq_2_file_out = re.sub('_L\d{3}_', '_LMerged_', fastq_2_file_out)

    with contextlib.nested(
        FixedGzip(fastq_1_file_out, 'w'),
        FixedGzip(fastq_2_file_out, 'w')
    ) as (write_f1, write_f2):

        # Statistics variables
        total = 0
        match = 0
        n_count = 0
        duplicate = 0

        # Loop over fastq files
        for fastq_1_file, fastq_2_file in zip(args.r1_fastq, args.r2_fastq):

            # Open input files
            with contextlib.nested(
                FixedGzip(fastq_1_file, 'r'),
                FixedGzip(fastq_2_file, 'r'),
            ) as (f1, f2):
                # Read in both fastq files per 4 lines [id, seq, +, qual]
                for fastq_1_lines, fastq_2_lines in izip(grouper(f1, 4, ''), grouper(f2, 4, '')):
                    total += 1
                    for mip in mips:

                        if args.uuid_read == 'R1':
                            if fastq_2_lines[1].startswith(mips[mip]['ext_probe']) and fastq_1_lines[1].startswith(mips[mip]['lig_probe_revcom'], args.uuid_length):
                                match += 1
                                uuid = fastq_1_lines[1][0:args.uuid_length]
                                # skip uuid containing 'N'
                                if "N" in uuid.upper():
                                    n_count += 1
                                    break
                                # Check duplicate reads, uuid must be unique per mip.
                                elif uuid in mips[mip]['uuids']:
                                    duplicate += 1
                                    mips[mip]['dup_count'] += 1
                                else:
                                    mips[mip]['uuids'].add(uuid)
                                    mips[mip]['count'] += 1
                                    # Trim fastq
                                    fastq_1_lines = list(fastq_1_lines)
                                    fastq_2_lines = list(fastq_2_lines)

                                    fastq_1_lines[1] = fastq_1_lines[1][len(mips[mip]['lig_probe_revcom'])+args.uuid_length:]  # seq
                                    fastq_1_lines[3] = fastq_1_lines[3][len(mips[mip]['lig_probe_revcom'])+args.uuid_length:]  # qual

                                    fastq_2_lines[1] = fastq_2_lines[1][len(mips[mip]['ext_probe']):]  # seq
                                    fastq_2_lines[3] = fastq_2_lines[3][len(mips[mip]['ext_probe']):]  # qual

                                    # Print fastq to new trimmed and dedupped fastq's.
                                    write_f1.write(''.join(fastq_1_lines))
                                    write_f2.write(''.join(fastq_2_lines))

                                # Track unique uuids in sample
                                if uuid not in unique_uuids:
                                    unique_uuids.add(uuid)
                                break  # A read can only belong to one mip thus break.

                        if args.uuid_read == 'R2':
                            if fastq_2_lines[1].startswith(mips[mip]['ext_probe'], args.uuid_length) and fastq_1_lines[1].startswith(mips[mip]['lig_probe_revcom']):
                                match += 1
                                uuid = fastq_2_lines[1][0:args.uuid_length]
                                # skip uuid containing 'N' or 'n'
                                if "N" in uuid.upper():
                                    n_count += 1
                                    break
                                # Check duplicate reads, uuid must be unique per mip.
                                elif uuid in mips[mip]['uuids']:
                                    duplicate += 1
                                    mips[mip]['dup_count'] += 1
                                else:
                                    mips[mip]['uuids'].add(uuid)
                                    mips[mip]['count'] += 1
                                    # Trim fastq
                                    fastq_1_lines = list(fastq_1_lines)
                                    fastq_2_lines = list(fastq_2_lines)

                                    fastq_1_lines[1] = fastq_1_lines[1][len(mips[mip]['lig_probe_revcom']):]  # seq
                                    fastq_1_lines[3] = fastq_1_lines[3][len(mips[mip]['lig_probe_revcom']):]  # qual

                                    fastq_2_lines[1] = fastq_2_lines[1][len(mips[mip]['ext_probe'])+args.uuid_length:]  # seq
                                    fastq_2_lines[3] = fastq_2_lines[3][len(mips[mip]['ext_probe'])+args.uuid_length:]  # qual

                                    # Print fastq to new trimmed and dedupped fastq's.
                                    write_f1.write(''.join(fastq_1_lines))
                                    write_f2.write(''.join(fastq_2_lines))

                                # Track unique uuids in sample
                                if uuid not in unique_uuids:
                                    unique_uuids.add(uuid)
                                break  # A read can only belong to one mip thus break.

    print 'Match with mip:', match
    print 'Reads with N in uuid', n_count
    print 'Duplicate reads', duplicate
    print 'total reads', total
    print 'sample_unique_uuid_count', len(unique_uuids)

    print 'mip\tuniqe_read_count\tdup_count\tuuids'
    for mip in mips:
        print '{0}\t{1}\t{2}\t{3}'.format(mip, mips[mip]['count'], mips[mip]['dup_count'], ','.join(mips[mip]['uuids']))
