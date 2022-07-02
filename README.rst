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

Currently, the only binning algorithms wrapped are MetaBAT2 and CONCOCT, but not for long!

Installation
------------

1. Clone repo from `github <https://github.com/lauren-mak/camp_binning>_`. 
    - Note: This is not a generic template for CAP2/CAMP modules, that's TBD. 

2. Set up the conda environment (contains, Snakemake) using ``configs/conda/camp_binning.yaml``. 
    - There are some compatibility issues that I haven't ironed out (samtools and bowtie2 due to RedHat's geriatric dependencies), so you may have to substitute in your own versions of those two tools. 

3. Make sure the installed pipeline works correctly. ``pytest`` only generates temporary outputs so no files should be created.
::
    git clone https://github.com/lauren-mak/camp_binning
    cd camp_binning
    conda env create -f configs/conda/camp_binning.yaml
    conda activate camp_binning
    pytest .tests/unit/

Using the Module
----------------

**Input**: ``/path/to/samples.csv`` provided by the user.

**Output**: 1) An output config file summarizing 2) the module's outputs. 

- ``/path/to/work/dir/binning/final_reports/samples.csv`` for ingestion by the next module (ex. quality-checking)
- ``/path/to/work/dir/binning/*/sample_name/``, where ``*`` is either ``1_metabat2`` or ``2_concoct``, the directories containing FastAs (``*.fa``) of MAGs inferred by MetaBAT2 and CONCOCT respectively

**Structure**:
::
    └── workflow
        ├── Snakefile
        ├── binning.py
        └── utils.py
- ``workflow/binning.py``: Click-based CLI that wraps the ``snakemake`` and unit test generation commands for clean management of parameters, resources, and environment variables.
- ``workflow/Snakefile``: The ``snakemake`` pipeline. 
- ``workflow/utils.py``: 

1. Make your own ``samples.csv`` based on the template in ``configs/samples.csv``. Sample test data can be found in ``.tests/unit/map_sort/data/work_dir/tmp/``.
    * ``samples.csv`` requires absolute paths to Illumina reads (currently, ``ingest_samples`` in ``workflow/utils.py`` expects FastQs) and de novo assembled contigs.  

2. Update the relevant ``metabat2`` and ``concoct`` parameters in ``configs/parameters.yaml``.

3. Update the computational resources available to the pipeline in ``resources/*.yaml`` where ``*`` is either 'slurm' or 'bash'. 

4. To run CAMP on the command line, use the following, where ``/path/to/work/dir`` is replaced with the absolute path of your chosen working directory, and ``/path/to/samples.csv`` is replaced with your copy of ``samples.csv``. 
::
    python /path/to/camp_binning/workflow/binning.py \
        -w /path/to/camp_binning/workflow/Snakefile \
        -d /path/to/work/dir \
        -s /path/to/samples.csv
- Note: This setup allows the main Snakefile to live outside of the work directory.

5. To run CAMP on a job submission cluster (for now, only Slurm is supported), use the following.
    * ``--slurm`` is an optional flag that submits all rules in the Snakemake pipeline as ``sbatch`` jobs. 
::
    sbatch -j jobname -e jobname.err.log -o jobname.out.log << "EOF"
    #!/bin/bash
    python /path/to/camp_binning/workflow/binning.py --slurm \
        -w /path/to/camp_binning/workflow/Snakefile \
        -d /path/to/work/dir \
        -s /path/to/samples.csv
    EOF


Extending the Module
--------------------

We love to see it! The module was partially envisioned as a dependable, prepackaged sandbox for developers to test their shiny new tools in. 

For Tool and Module Developers
------------------------------

These instructions are meant for developers who have made a tool and want to integrate or demo its functionality as part of a standard metagenomics workflow, or developers who want to integrate an existing tool. 

1. Write a module rule that wraps your tool and integrates its input and output into the pipeline. 
    * This is a great `Snakemake tutorial <https://bluegenes.github.io/hpc-snakemake-tips/>`_ for writing basic Snakemake rules.
    * If you're adding new tools from an existing YAML, use ``conda env update --file configs/conda/camp_binning.yaml --prune``.
2. Update the ``make_config`` in ``workflow/Snakefile`` rule to check for your tool's output files. Update ``samples.csv`` to document its output if downstream modules/tools are meant to ingest it. 
3. If applicable, update the default conda config using ``conda env export > config/conda/camp_binning.yaml`` with your tool and its dependencies. 
4. Add your tool's installation and running instructions to the module documentation. 
5. Run the pipeline once through to make sure everything works using the test data in ``.tests/unit/map_sort/data/work_dir/tmp/``. Then, generate unit tests to ensure that others can sanity-check their installations.
::
    python /path/to/camp_binning/workflow/binning.py generate_unit_tests \
        -w /path/to/camp_binning/workflow/Snakefile \
        -s /path/to/samples.csv

6. Increment the version number of the modular pipeline by using ``bumpversion minor``.
7. If you want your tool integrated into the main CAP2/CAMP pipeline, send a pull request and we'll have a look at it ASAP! 
    - Please make it clear what your tool intends to do by including a summary in the commit/pull request (ex. "Release X.Y.Z: Integration of tool A, which does B to C and outputs D").

For Pipeline Extenders
----------------------

These instructions are meant for developers who want to modify any part of the module/pipeline's internal structures and reporting procedures. These include but are not limited to: Changes to the working directory organization, file-naming conventions, logging procedures, documentation structures. Please do everything from step 5 through 7 in the above section (as well as step 4 if your structural alterations depend on any additional packages). 

Bugs
----

There is a dependency error that hasn't been addressed yet, namely...
- ``bowtie2`` in the main ``camp_binning`` conda environment, which has conflicting C++ and Perl dependencies with some other packges


* Free software: MIT license
* Documentation: https://camp-binning.readthedocs.io.

