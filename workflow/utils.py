'''Utilities.'''


# --- Workflow setup --- #


import gzip
import os
from os import makedirs, symlink
from os.path import abspath, basename, exists, join
import pandas as pd
import shutil


def extract_from_gzip(p, out):
    ap = abspath(p)
    if open(ap, 'rb').read(2) == b'\x1f\x8b': # If the input is gzipped
        with gzip.open(ap, 'rb') as f_in, open(out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    else: # Otherwise, symlink
        symlink(ap, out)


def ingest_samples(samples, tmp):
    df = pd.read_csv(samples, header = 0, index_col = 0) # name, ctgs, fwd, rev
    s = list(df.index)
    lst = df.values.tolist()
    for i,l in enumerate(lst):
        if not exists(join(tmp, s[i] + '.fasta')):
            symlink(abspath(l[0]), join(tmp, s[i] + '.fasta'))
            extract_from_gzip(abspath(l[1]), join(tmp, s[i] + '_1.fastq'))
            extract_from_gzip(abspath(l[2]), join(tmp, s[i] + '_2.fastq'))
    return s


class Workflow_Dirs:
    '''Management of the working directory tree.'''
    OUT = ''
    TMP = ''
    LOG = ''

    def __init__(self, work_dir, module):
        self.OUT = join(work_dir, module)
        self.TMP = join(work_dir, 'tmp') 
        self.LOG = join(work_dir, 'logs') 
        if not exists(self.OUT):
            makedirs(self.OUT)
            makedirs(join(self.OUT, '0_contig_coverage'))
            makedirs(join(self.OUT, '1_metabat2'))
            makedirs(join(self.OUT, '2_concoct'))
            makedirs(join(self.OUT, '3_vamb'))
            makedirs(join(self.OUT, 'final_reports'))
        if not exists(self.TMP):
            makedirs(self.TMP)
        if not exists(self.LOG):
            makedirs(self.LOG)
            makedirs(join(self.LOG, 'map_sort'))
            makedirs(join(self.LOG, 'calculate_depth'))
            makedirs(join(self.LOG, 'metabat2_binning'))
            makedirs(join(self.LOG, 'concoct_binning'))
            makedirs(join(self.LOG, 'vamb_binning'))
            makedirs(join(self.LOG, 'make_config'))


def cleanup_files(work_dir, df):
    smps = list(df.index)
    for s in smps:
        os.remove(join(work_dir, 'binning', '0_contig_coverage', s, 'coverage.bam'))
        os.remove(join(work_dir, 'binning', '0_contig_coverage', s, 'coverage.bam.bai'))

        
def print_cmds(log):
    fo = basename(log).split('.')[0] + '.cmds'
    lines = open(log, 'r').read().split('\n')
    fi = [l for l in lines if l != '']
    write = False
    with open(fo, 'w') as f_out:
        for l in fi:
            if 'rule' in l:
                f_out.write('# ' + l.strip().replace('rule ', '').replace(':', '') + '\n')
            if 'wildcards' in l: 
                f_out.write('# ' + l.strip().replace('wildcards: ', '') + '\n')
            if 'resources' in l:
                write = True 
                l = ''
            if '[' in l: 
                write = False 
            if write:
                f_out.write(l.strip() + '\n')
            if 'rule make_config' in l:
                break


# --- Workflow functions --- #


from Bio import SeqIO
from collections import Counter
from io import StringIO
from os.path import basename, splitext
import re
import subprocess
import sys


def chunks(l, n, o):
    # Yield successive n-sized chunks from l with given overlap o between the chunks.
    assert n > o
    for i in range(0, len(l) - n + 1, n - o):
        yield l[i:i + n] if i + n + n - o <= len(l) else l[i:]


def cut_up_fasta(ctg, frag_size, olap_size, out_dir, out_fa, out_bed):
    '''Split up assembly contigs into windows of 'frag_size' bp 
    with 'olap_size' overlap.'''
    if not exists(out_dir):
        makedirs(out_dir)
    with open(out_fa, 'w') as of, open(out_bed, 'w') as ob:
        for r in SeqIO.parse(ctg, "fasta"):
            if len(r.seq) >= 2 * frag_size:
                i = 0
                for split_seq in chunks(r.seq, frag_size, olap_size):
                    print(">{}.concoct_part_{}\n{}".\
                        format(r.id, i, split_seq), file = of)
                    print("{0}\t{2}\t{3}\t{0}.concoct_part_{1}".\
                        format(r.id, i, frag_size*i, frag_size*i+len(split_seq)),\
                        file = ob)
                    i += 1
            else:
                print(">{}.concoct_part_0\n{}".\
                        format(r.id, r.seq), file = of)
                print("{0}\t0\t{1}\t{0}.concoct_part_0".format(r.id, len(r.seq)),\
                    file = ob)


def make_concoct_table(in_bed, in_bam, output):
    '''Reads input files into dictionaries then prints everything in the table
    format required for running CONCOCT.'''
    p = subprocess.Popen(["samtools", "bedcov", in_bed, in_bam], \
        stdout = subprocess.PIPE)
    out, err = p.communicate()
    # Header
    col_names = [splitext(basename(in_bam))[0]] # Use index if no sample names given in header
    header = ["cov_mean_sample_{}".format(n) for n in col_names]
    # Content
    fh = StringIO(out.decode('utf-8'))
    df = pd.read_table(fh, header=None)
    avg_coverage_depth = df[df.columns[4:]].divide((df[2]-df[1]), axis=0)
    avg_coverage_depth.index = df[3]
    avg_coverage_depth.columns = header 
    avg_coverage_depth.to_csv(output, index_label='contig', sep='\t', \
        float_format='%.3f')


def extract_bin_id(contig_id):
    CONTIG_PART_EXPR = re.compile("(.*)\.concoct_part_([0-9]*)")
    n = contig_id.split('.')[-1]
    try:
        original_contig_id, part_id = CONTIG_PART_EXPR.match(contig_id).group(1,2)
        return [original_contig_id, part_id]
    except AttributeError: # No matches for concoct_part regex
        return contig_id, 0


def split_concoct_output(concoct, ctg, out_dir, output):
    # Match CONCOCT bin labels to the original contig IDs
    df = pd.read_csv(concoct, header = 0) # contig_id,cluster_id
    new_cols = df.apply(lambda row : extract_bin_id(row['contig_id']), axis = 1)
    df['original_contig_id'] = [i[0] for i in new_cols]
    df['part_id'] = [i[1] for i in new_cols]
    original_to_concoct = {}
    # Find the best bin label for each original contig
    cluster_mapping = {}
    for curr_ctg in df.original_contig_id.unique(): # For each original contig...
        sub_df = df[df['original_contig_id'] == curr_ctg]
        if sub_df.shape[1] > 1: # If there are multiple assignments
            c = Counter(list(sub_df['cluster_id']))
            majority_vote = c.most_common(1)[0][0]
            possible_bins = [(a,b) for a, b in c.items()]
            if len(c.values()) > 1:
                sys.stderr.write('No consensus cluster for \
                    contig {}: {}\t CONCOCT cluster: {}\n'\
                    .format(curr_ctg, possible_bins, majority_vote))
        else:
            majority_vote = list(sub_df['cluster_id'])[0]
        cluster_mapping[curr_ctg] = majority_vote
    # Split the assembly FastA into separate bin FastAs
    current_bin = ''
    for line in open(ctg):
        if line.startswith('>'):
            if current_bin != '': 
                f.close()
            contig = line[1:-1].split('.')[0].split()[0]
            line = line.rsplit()[0] + '\n'
            if contig in cluster_mapping: 
                current_bin = 'bin.' + str(cluster_mapping[contig]) + '.fa'
            else: 
                current_bin = 'unbinned.fa'
            f = open(out_dir + '/' + current_bin, 'a')
        f.write(line)



