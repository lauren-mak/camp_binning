.. highlight:: shell

============
Installation
============


Stable release
--------------

1. Clone repo from `github <https://github.com/lauren-mak/camp_binning>_`. 

2. Set up the conda environment (contains, Snakemake) using ``configs/conda/camp_binning.yaml``. 
    - There are some compatibility issues that I haven't ironed out (samtools and bowtie2 due to RedHat's geriatric dependencies), so you may have to substitute in your own versions of those two tools. 

3. Make sure the installed pipeline works correctly. ``pytest`` only generates temporary outputs so no files should be created.
::
    cd camp_binning
    conda env create -f configs/conda/camp_binning.yaml
    conda activate camp_binning
    pytest .tests/unit/
