# mips
Scripts/tools to work with mip experiments.

# Usage
## Per sample
```bash
python mips_trim_dedup.py design.txt R1.fastq R2.fastq
```
## Qsub run to UMCU hpc
```bash
python qsub_mips_trim_dedup.py /path/to/design.txt /path/to/raw_data/sequencer/run/Unaligned/project /path/to/output/folder
```
