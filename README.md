# mips
Scripts/tools for working with mip experiments.

# Usage
## Per sample
```bash
python mips_trim_dedup.py -d design.txt -r1 [R1.fastq [R1.fastq ...]] -r2 [R2.fastq [R2.fastq ...]] -l UUID_LENGTH -ur {R1,R2}
```
## Qsub run to UMCU hpc
```bash
python qsub_*.py  /path/to/design.txt uuid_length uuid_read(R1,R2) /path/to/raw_data/sequencer/run/Data/Intensities/BaseCalls /path/to/output/folder
```
