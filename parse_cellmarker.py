# build a database using cellmarker for... something?
from collections import defaultdict
import sqlite3
import pandas as pd

data = pd.read_table('all_cell_markers.txt')

SELECTED_SPECIES = 'human'

conn = sqlite3.connect('cellmarker/data/cell_marker.db')
c = conn.cursor()
#try:
#    data.to_sql('all_cell_markers', conn)
#except ValueError as e:
#    pass
#try:
#    c.execute('CREATE INDEX gene_symbol_index ON all_cell_markers("geneSymbol")')
#except:
#    pass
#try:
#    c.execute('CREATE INDEX cellName_index ON all_cell_markers("cellName")')
#except:
#    pass
#try:
#    c.execute('CREATE INDEX entry_index ON all_cell_markers("index_labels")')
#except:
#    pass

# build a mapping of gene markers to cell types, and a map of cell types to gene markers.
# TODO: do genes with more references get more weights?
genes_to_cells = defaultdict(lambda: set())
genes_to_tissues = defaultdict(lambda: set())
cells_to_genes = defaultdict(lambda: set())
tissues_to_genes = defaultdict(lambda: set())
genes_to_indices = defaultdict(lambda: [])
cells_genes_to_pmids = defaultdict(lambda: set())
cells_to_cellonto = dict()
for i, row in data.iterrows():
    # one of 'Human' or 'Mouse'
    species = row['speciesType']
    tissue = row['tissueType']
    # one of 'Normal cell' or 'Cancer cell'
    cell_type = row['cellType']
    cell_name = row['cellName']
    gene_symbol = row['geneSymbol']
    protein_name = row['proteinName']
    pmid = row['PMID']
    if pmid == 'Company':
        pmid = row['Company']
        print(pmid)
    if not isinstance(gene_symbol, str):
        continue
    gene_symbols = [gene_symbol]
    if ',' in gene_symbol:
        gene_symbols = [x.strip(' []') for x in gene_symbol.split(',')]
    gene_symbols = [x.upper() for x in gene_symbols]
    cell_marker = row['cellMarker']
    if isinstance(cell_marker, str):
        cell_markers = [cell_marker]
        if ',' in cell_marker:
            cell_markers = [x.strip(' []') for x in cell_marker.split(',')]
        gene_symbols += [x.upper() for x in cell_markers]
    uberon_id = row['UberonOntologyID']
    cell_ontology_id = row['CellOntologyID']
    if isinstance(cell_ontology_id, str):
        cells_to_cellonto[cell_name] = cell_ontology_id
    for gene_symbol in set(gene_symbols):
        if gene_symbol == 'NA':
            continue
        genes_to_indices[gene_symbol].append(i)
        cells_to_genes[cell_name, species].add((gene_symbol))
        genes_to_cells[gene_symbol, species].add((cell_name))
        genes_to_tissues[gene_symbol, species].add((tissue))
        tissues_to_genes[tissue, species].add((gene_symbol))
        cells_genes_to_pmids[(cell_name, gene_symbol, species)].add(pmid)
        cells_genes_to_pmids[(tissue, gene_symbol, species)].add(pmid)

# create a table representing a gene-index mapping...
try:
    c.execute('CREATE TABLE gene_indices (gene text, row_id integer)')
    for gene, indices in genes_to_indices.items():
        for index in indices:
            c.execute('INSERT INTO gene_indices VALUES (?, ?)', (gene, index))
except:
    pass
try:
    c.execute('CREATE INDEX gene_indices_index ON gene_indices(gene)')
except:
    pass

# TODO: separate human and mouse datasets...
# create a table representing a cell type - gene mapping.
try:
    c.execute('CREATE TABLE cell_gene(cellName text, species text, gene text)')
    for cell, genes in cells_to_genes.items():
        cell, species = cell
        for gene in genes:
            c.execute('INSERT INTO cell_gene VALUES (?, ?, ?)', (cell, species, gene))
except:
    pass
try:
    c.execute('CREATE INDEX cell_names_index ON cell_gene(cellName, species)')
except:
    pass

# create a table representing a tissue - gene mapping.
try:
    c.execute('CREATE TABLE tissue_gene (tissueType text, species text, gene text)')
    for tissue, genes in tissues_to_genes.items():
        tissue, species = tissue
        for gene in genes:
            c.execute('INSERT INTO tissue_gene VALUES (?, ?, ?)', (tissue, species, gene))
except:
    pass
try:
    c.execute('CREATE INDEX tissue_type_index ON tissue_gene(tissueType, species)')
except:
    pass

# create a table represent a cell name - cell ontology ID mapping
try:
    c.execute('CREATE TABLE cell_cl (cellName text, CellOntologyID text)')
    for cell_name, onto_id in cells_to_cellonto.items():
        c.execute('INSERT INTO cell_cl VALUES (?, ?)', (cell_name, onto_id))
except:
    pass
try:
    c.execute('CREATE INDEX cell_cl_index ON cell_cl(cellName)')
except:
    pass

# create a table representing a cellName-gene : PMID mapping.
try:
    c.execute('CREATE TABLE cell_gene_pmid (cellName text, gene text, species text, pmid text)')
    for cell_gene, pmids in cells_genes_to_pmids.items():
        cell, gene, species = cell_gene
        for pmid in pmids:
            c.execute('INSERT INTO cell_gene_pmid VALUES (?, ?, ?, ?)', (cell, gene, species, pmid))
except:
    pass
try:
    c.execute('CREATE INDEX cell_gene_pmid_index ON cell_gene_pmid(cellName, gene, species)')
except:
    pass

conn.commit()
conn.close()

# TODO: do some sort of hypergeometric test???
# given a list of genes, we want to find both tissue types and cell names that are overrepresented.
# how do we do that???
# how do we calculate p-values for this thing?
