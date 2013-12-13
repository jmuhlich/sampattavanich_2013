import sys
import os
import codecs
import errno
import shutil
import stat
import argparse
import pandas as pd
import openpyxl
import jinja2


RESOURCE_PATH = (
    '/home/jmuhlich/Volumes/sysbio on research.files.med.harvard.edu/'
    'SORGER PROJECTS/Publications/2013/Submissions/'
    'SampattavanichAndKramer_et_al-FOXO3a/websites'
    )

PLATEMAP_FILENAME = os.path.join(RESOURCE_PATH, 'Platemap.xlsx')
CELL_IMAGE_PATH = os.path.join(RESOURCE_PATH,
                               'PNG_individual_timeSeries_short_noTickLabel')
CELL_IMAGE_PREFIX = 'Individual_nolabel_'
POPUP_IMAGE_PATH = os.path.join(RESOURCE_PATH, 'PNG_individual_wellAveraged')

LIGAND_RENAMES = {
    'None': '',
    'IGF': 'IGF1',
    }

INHIBITOR_RENAMES = {
    'None': '',
    }

FLOAT_COLUMNS = ['ligand_conc', 'inhibitor_conc']

LIGAND_ORDER = ['IGF1', 'HRG', 'HGF', 'EGF', 'FGF', 'BTC', 'EPR']


def main(argv):
    argparser = argparse.ArgumentParser()
    argparser.add_argument( '-m', '--minimal', action='store_true',
                           help="minimal mode (don't copy media files)")
    args = argparser.parse_args()

    platemap = build_platemap(PLATEMAP_FILENAME)
    ligand_concs = [c for c in sorted(platemap.ligand_conc.unique()) if c > 0]
    rc_address = []
    for row, ligand_conc in enumerate(ligand_concs):
        rc_address_row = []
        for col, ligand in enumerate(LIGAND_ORDER):
            location = ((platemap.ligand_conc == ligand_conc) &
                        (platemap.ligand == ligand))
            address = platemap[location].rc_address.iat[0]
            rc_address_row.append(address)
        rc_address.append(rc_address_row)
            
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates')
        )
    template = template_env.get_template('table.html')
    data = {'ligands': LIGAND_ORDER,
            'ligand_concs': ligand_concs,
            'rc_address': rc_address,
            }
    content = template.render(data)

    makedirs_exist_ok('output')
    with codecs.open('output/table.html', 'w', 'utf-8') as out_file:
        out_file.write(content)
    shutil.copy('static/style.css', 'output')
    shutil.copy('static/main.js', 'output')

    if not args.minimal:
        makedirs_exist_ok('output/img/cell')
        for src_filename in os.listdir(CELL_IMAGE_PATH):
            if not src_filename.endswith('.png'):
                continue
            src_path = os.path.join(CELL_IMAGE_PATH, src_filename)
            dest_filename = src_filename.partition(CELL_IMAGE_PREFIX)[2]
            dest_path = os.path.join('output', 'img', 'cell', dest_filename)
            shutil.copy(src_path, dest_path)
            os.chmod(dest_path, 0644)
        makedirs_exist_ok('output/img/popup')
        for src_filename in os.listdir(POPUP_IMAGE_PATH):
            if not src_filename.endswith('.png'):
                continue
            src_path = os.path.join(POPUP_IMAGE_PATH, src_filename)
            dest_filename = src_filename
            dest_path = os.path.join('output', 'img', 'popup', dest_filename)
            shutil.copy(src_path, dest_path)
            os.chmod(dest_path, 0644)

    return 0


"""Build plate-map dataframe."""
def build_platemap(filename):

    wb = openpyxl.load_workbook(filename)
    ws = wb.worksheets[0]

    # Extract row metadata.
    row_meta = dataframe_for_range(ws, 'D9:D16')
    row_meta.columns = pd.Index(['ligand'])
    row_meta['ligand'].replace(LIGAND_RENAMES, inplace=True)
    row_meta.insert(0, 'plate_row', range(1, len(row_meta)+1))

    # Extract column metadata.
    col_meta = dataframe_for_range(ws, 'G4:R6').T
    col_meta.columns = pd.Index(['ligand_conc', 'inhibitor',
                                 'inhibitor_conc'])
    col_meta['inhibitor'].replace(INHIBITOR_RENAMES, inplace=True)
    for name in FLOAT_COLUMNS:
        col_meta[name] = col_meta[name].astype(float)
    col_meta.insert(0, 'plate_col', range(1, len(col_meta)+1))

    # Add same-valued dummy columns so merge() will generate a full cartesian
    # product, then delete that column in the resulting dataframe.
    row_meta.insert(0, 'dummy', [0] * len(row_meta))
    col_meta.insert(0, 'dummy', [0] * len(col_meta))
    platemap = pd.merge(row_meta, col_meta, on='dummy')
    del platemap['dummy']

    # Swap the columns around a bit to move the row and column numbers up front.
    new_column_order = platemap.columns[[0,2,1]].append(platemap.columns[3:])
    platemap = platemap[new_column_order]

    # Get rid of extreme left/right/bottom cells -- not part of the experiment.
    platemap = platemap[(platemap.plate_col >= 2) &
                        (platemap.plate_col <= 11) &
                        (platemap.plate_row <= 7)]

    # Replace plate_row and plate_col with a new column in r1c1 format.
    rc_values = platemap.apply(lambda r: 'r%(plate_row)dc%(plate_col)d' % r,
                               axis=1)
    platemap = platemap.drop(['plate_row', 'plate_col'], axis=1)
    platemap.insert(0, 'rc_address', rc_values)

    return platemap


"""Return a Pandas DataFrame from a given range in an openpyxl worksheet."""
def dataframe_for_range(worksheet, range):
    data = [[c.value for c in row] for row in worksheet.range(range)]
    return pd.DataFrame(data)


def makedirs_exist_ok(name):
    try:
        os.makedirs(name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
