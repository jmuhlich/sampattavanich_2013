import sys
import pandas as pd
import openpyxl


PLATEMAP_FILENAME = (
    '/home/jmuhlich/Volumes/sysbio on research.files.med.harvard.edu/'
    'SORGER PROJECTS/Publications/2013/Submissions/'
    'SampattavanichAndKramer_et_al-FOXO3a/websites/Platemap.xlsx')


def main(argv):
    return 0


"""Build plate-map dataframe."""
def build_platemap(filename):

    wb = openpyxl.load_workbook(filename)
    ws = wb.worksheets[0]

    # Extract row metadata.
    row_meta = dataframe_for_range(ws, 'D9:D16')
    row_meta.columns = pd.Index(['ligand'])
    row_meta['ligand'].replace('None', '', inplace=True)
    row_meta.insert(0, 'plate_row', range(1, len(row_meta)+1))

    # Extract column metadata.
    col_meta = dataframe_for_range(ws, 'G4:R6').T
    col_meta.columns = pd.Index(['ligand_conc', 'inhibitor',
                                 'inhibitor_conc'])
    col_meta['inhibitor'].replace('None', '', inplace=True)
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

    # Synthesize a new column in r1c1 format.
    rc_values = platemap.apply(lambda r: 'r%(plate_row)dc%(plate_col)d' % r, axis=1)
    platemap.insert(2, 'rc_address', rc_values)

    return platemap


"""Return a Pandas DataFrame from a given range in an openpyxl worksheet."""
def dataframe_for_range(worksheet, range):
    data = [[c.value for c in row] for row in worksheet.range(range)]
    return pd.DataFrame(data)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
