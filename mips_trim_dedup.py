#!/usr/bin/env python

import sys
from itertools import izip_longest, izip
import gzip
import contextlib

def reverse_complement(seq):
    """
    Return reverse complement of a dna sequence.
    """
    bases_dict = {
        'A':'T', 'a':'t',
        'C':'G', 'g':'c',
        'G':'C', 'c':'g',
        'T':'A', 't':'a'}
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
                'ext_probe':ext_probe, 'ext_probe_revcom':ext_probe_revcom,
                'lig_probe':lig_probe, 'lig_probe_revcom':lig_probe_revcom,
                'uuids':set({}),
                'count':0, 'dup_count':0
            }

    return mips

def grouper(iterable, n, fillvalue=None):
    """
    Helper function to read in fasta file per 4 lines.
    """
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

class FixedGzip(gzip.GzipFile):
    """
    Fix gzip class to work with contextlib.nested in python 2.6
    """
    def __enter__(self):
        if self.fileobj is None:
            raise ValueError("I/O operation on closed GzipFile object")
        return self

    def __exit__(self, *args):
        self.close()

if __name__ == "__main__":

    # Parse arguments
    if len(sys.argv) != 4:
        print "python mips_trim_dedup.py design.txt R1.fastq R2.fastq"
        sys.exit()

    design_file = sys.argv[1]
    mips = parse_design(design_file)

    fasta_1_file = sys.argv[2]
    fasta_2_file = sys.argv[3]

    fasta_1_file_out = fasta_1_file.split('/')
    fasta_1_file_out = "trimmed-dedup-"+fasta_1_file_out[-1]
    fasta_2_file_out = fasta_2_file.split('/')
    fasta_2_file_out = "trimmed-dedup-"+fasta_2_file_out[-1]

    total = 0
    match = 0
    duplicate = 0

    # Open input and output files
    with contextlib.nested(
        FixedGzip(fasta_1_file, 'r'),
        FixedGzip(fasta_2_file, 'r'),
        FixedGzip(fasta_1_file_out, 'w'),
        FixedGzip(fasta_2_file_out, 'w')
        ) as (f1, f2, write_f1, write_f2):
        # Read in both fasta files per 4 lines id seq + qual
        for fasta_1_lines, fasta_2_lines in izip(grouper(f1, 4, ''), grouper(f2, 4, '')):
            total += 1
            for mip in mips:
                if fasta_2_lines[1].startswith(mips[mip]['ext_probe'],6) and fasta_1_lines[1].startswith(mips[mip]['lig_probe_revcom']):
                    match += 1
                    uuid = fasta_2_lines[1][0:6] # uuid length
                    # Check duplicate reads, uuid must be unique per mip.
                    if uuid in mips[mip]['uuids']:
                        duplicate += 1
                        mips[mip]['dup_count'] += 1
                    else :
                        mips[mip]['uuids'].add(uuid)
                        mips[mip]['count'] += 1
                        #Trim fastq
                        fasta_1_lines = list(fasta_1_lines)
                        fasta_2_lines = list(fasta_2_lines)

                        fasta_1_lines[1] = fasta_1_lines[1][len(mips[mip]['lig_probe_revcom']):]#seq
                        fasta_1_lines[3] = fasta_1_lines[3][len(mips[mip]['lig_probe_revcom']):]#qual

                        fasta_2_lines[1] = fasta_2_lines[1][len(mips[mip]['ext_probe'])+5:]#seq
                        fasta_2_lines[3] = fasta_2_lines[3][len(mips[mip]['ext_probe'])+5:]#qual

                        ## Print fastq to new trimmed and dedupped fastq's.
                        write_f1.write(''.join(fasta_1_lines))
                        write_f2.write(''.join(fasta_2_lines))
                    break

    print 'match:', match
    print 'duplicate', duplicate
    print 'total', total

    print 'mip\tread_count\tdup_count'
    for mip in mips:
        print '{0}\t{1}\t{2}'.format(mip, mips[mip]['count'], mips[mip]['dup_count'])
