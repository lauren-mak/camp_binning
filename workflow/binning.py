"""CLI for the CAMP binning module."""

import click
from os.path import abspath, join
from utils import *


def pipeline(workflow, work_dir, samples, slurm, cap2, unit_test):
    # Load and/or make the working directory structure
    d = Workflow_Dirs(workflow, work_dir, samples)

    # Load sample names and input files 
    s = ingest_samples(samples, d.TMP)

    # Get the absolute path of the Snakefile to find the profile configs
    bin_dir = abspath(workflow).split('/')[:-2] # /path/to/bin_dir/workflow/Snakefile
    method = 'slurm' if slurm else 'bash'
    p = join('/', *bin_dir, 'configs', method, 'config.yaml')

    # Load program parameters and resources
    pyaml = join(*bin_dir, 'configs', 'parameters.yaml')
    ryaml = join(*bin_dir, 'configs', 'resources.yaml')

    # Set up the conda environment directory
    env_dir = join(*bin_dir, 'conda_envs')
    if not exists(env_dir):
        makedirs(env_dir)

    # Run workflow
    snakemake(
        workflow,
        profile = p,
        config = {
            'dirs': d,
            'SAMPLES': s,
            'cap2': cap2,
            'env_yamls': join(*bin_dir, 'configs', 'conda')
        },
        configfiles = [
            pyaml,
            ryaml
        ],
        use_conda = True,
        conda_prefix = env_dir,
        conda_cleanup_pkgs = cache,
        generate_unit_tests = unit_test
    )


@click.command()
@click.option('-w', '--workflow', type = click.Path(), required = True, \
    help = 'Absolute path to the Snakefile')
@click.option('-d', '--work_dir', type = click.Path(), required = True, \
    help = 'Absolute path to working directory')
@click.option('-s', '--samples', type = click.Path(), required = True, \
    help = 'Sample CSV in format [sample_name,contig_fasta,fwd_fastq,rev_fastq]')
@click.option('--slurm', is_flag = True, \
    help = 'Run workflow by submitting rules as Slurm cluster jobs')
@click.option('--cap2', is_flag = True, \
    help = 'Run workflow in CAP2 mode')
def run(workflow, work_dir, samples, slurm, cap2):
    pipeline(workflow, work_dir, samples, slurm, cap2, None)


@click.command()
@click.option('-w', '--workflow', type = click.Path(), required = True, \
    help = 'Absolute path to the Snakefile')
def generate_unit_tests(workflow):
    bin_dir = abspath(workflow).split('/')[:-2] # /path/to/bin_dir/workflow/Snakefile
    samples = join(*bin_dir, 'contigs', 'samples.csv')
    pipeline(workflow, bin_dir, samples, False, False, True)


if __name__ == "__main__":
    run()
