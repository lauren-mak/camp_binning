============
CAMP Binning
============


.. image:: https://readthedocs.org/projects/camp-binning/badge/?version=latest
        :target: https://camp-binning.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/version-0.1.0-brightgreen


Overview
--------

This module is designed to function as both a standalone MAG binning pipeline as well as a component of the larger CAP2/CAMP metagenome analysis pipeline. As such, it is both self-contained (ex. instructions included for the setup of a versioned environment, etc.), and seamlessly compatible with other CAMP modules (ex. ingests and spawns standardized input/output config files, etc.). 

As far as the binning procedure goes, the design philosophy is just to replicate the functionality of MetaWRAP (one of the original ensemble `binning methods <https://github.com/bxlab/metaWRAP>`_) with i) better dependency conflict management and ii) improved integration with new binning algorithms. 

Currently, the only binning algorithm included is MetaBAT2, but not for long!

Installation
------------

1. Clone repo from github (https://github.com/lauren-mak/camp_binning). 
    - Note: This is not a generic template for CAP2/CAMP modules, that's TBD. 

2. Set up the conda environment (contains, Snakemake) using ``configs/conda.yaml``. 
    - There are some compatibility issues that I haven't ironed out (samtools and bowtie2 due to RedHat's geriatric dependencies), so you may have to substitute in your own versions of those two tools. 

3. Make sure the installed pipeline works correctly. ``pytest`` only generates temporary outputs so no files should be created.
::
    git clone https://github.com/lauren-mak/camp_binning
    cd camp_binning
    conda env create -f configs/conda.yaml
    conda activate camp_binning
    pytest .test/unit/

Using the Module
----------------

**Input**: ``/path/to/samples.csv`` provided by the user.

**Output**: 1) An output config file summarizing 2) the module's outputs. 

- ``/path/to/work/dir/binning/final_reports/sample.csv`` for ingestion by the next module (ex. quality-checking)
- ``/path/to/work/dir/binning/1_metabat2``, the directory containing FastAs (``*.fa``) of MAGs inferred by MetaBAT2
- Note: In the future, this location and the contents may change as more binning algorithms are added. 

1. Make your own ``samples.csv`` based on the template in ``configs/samples.csv``. Sample test data can be found in ``.tests/unit/map_sort/data/work_dir/tmp/``.
    - ``samples.csv`` requires absolute paths to Illumina reads (currently, ``ingest_samples`` in ``workflow/utils.py`` expects FastQs) and de novo assembled contigs.  

2. Update the relevant ``metabat2`` parameters in ``configs/parameters.yaml``.
    - Currently, only ``min_contig_len`` (minimum contig length to be considered for binning) is exposed. 

3. Update the computational resources available to the pipeline in ``configs/resources.yaml``. 
    - Advanced: Update job submission parameters (ex. maximum number of jobs to submit at once) in ``configs/*/config.yaml``. See `here <https://github.com/Snakemake-Profiles/slurm>`_ for more information on Snakemake profiles.

4. Run the following commands, where ``/path/to/work/dir`` is replaced with the absolute path of your chosen working directory, ``/path/to/samples.csv`` is replaced with your copy of ``samples.csv``, and ``bash_or_slurm`` is replaced with the appropriate job submission conditions. 
::
        snakemake -s /path/to/camp_binning/workflow/Snakefile \
                  --profile /path/to/camp_binning/configs/bash_or_slurm \
                  --config {"work_dir"="/path/to/work/dir", \
                            "samples"="/path/to/samples.csv"}
- In future versions, the messy ``--config`` switch that Snakemake uses will be cleaned up with a Click-based CLI. 
- This setup allows the main Snakefile to live outside of the work directory.

Extending the Module
--------------------

We love to see it! The module was partially envisioned as a dependable, prepackaged sandbox for developers to test their shiny new tools in. 

For Tool and Module Developers
------------------------------

These instructions are meant for developers who have made a tool and want to integrate or demo its functionality as part of a standard metagenomics workflow, or developers who want to integrate an existing tool. 

1. Write a module rule that wraps your tool and integrates its input and output into the pipeline. This is a great `Snakemake tutorial <https://bluegenes.github.io/hpc-snakemake-tips/>`_ for writing basic Snakemake rules.
2. Update the ``make_config`` in ``workflow/Snakefile`` rule to check for your tool's output files. Update ``sample.csv`` to document its output if downstream modules/tools are meant to ingest it. 
3. Update the ``config/conda.yaml`` with your tool's dependencies. 
4. Add your tool's installation and running instructions to the module documentation. 
    - Ideally, your tool is installable through ``conda``. If so, just add it to ``configs/conda.yaml`` and you're good to go! 

5. Run the pipeline once through to make sure everything works. Then, generate unit tests to ensure that others can sanity-check their installations.
::
        snakemake -s /path/to/camp_binning/workflow/Snakefile \
                  --profile /path/to/camp_binning/configs/bash_or_slurm \
                  --config {"work_dir"="/path/to/work/dir", \
                            "samples"="/path/to/samples.csv"} \
                  --generate-unit-tests 

6. Increment the version number of the modular pipeline by using ``bumpversion minor``.
7. If you want your tool integrated into the main CAP2/CAMP pipeline, send a pull request and we'll have a look at it ASAP! 
    - Please make it clear what your tool intends to do by including a summary in the commit/pull request (ex. "Release X.Y.Z: Integration of tool A, which does B to C and outputs D").

For Pipeline Extenders
----------------------

These instructions are meant for developers who want to modify any part of the module/pipeline's internal structures and reporting procedures. These include but are not limited to: Changes to the working directory organization, file-naming conventions, logging procedures, documentation structures. Please do everything from step 5 through 7 in the above section (as well as step 4 if your structural alterations depend on any additional packages). 

* Free software: MIT license
* Documentation: https://camp-binning.readthedocs.io.

