"""
Unit Hydrograph Output Parser

This script parses output files from a unit hydrograph model, extracts relevant
flow data, and prints the extracted data to the console. Optionally, the results
can be written to a combined spreadsheet.

Run the script from the command line with:
    python uhparse.py <path1> <path2> ... [-d DIGITS] [-p]

To use the more concise "uhparse" command, add the RMParse repository to the Path environment
variable.
"""

import sys
import re
import csv
import argparse
import warnings
from pathlib import Path
from typing import Tuple, List

from tabulate import tabulate

TABLE_START_FLAG = 'R u n o f f      H y d r o g r a p h'
TABLE_START_OFFSET = 7
TABLE_END_FLAG = '-----------------------------------------------------------------------'
TABLE_END_OFFSET = 0
TABLE_PATTERN = r'\s*(\d+\+\s*\d+)\s+([\d.]+)\s+([\d.]+).*'

def main() -> None:
    """Parse unit hydrograph output files, print to console, and write to csv."""
    filepaths, save, precision = parse_args()
    data = []
    for filepath in filepaths:
        print(f'Parsing file {filepath.name}')
        lines = read_file(filepath)
        peak_flowrate, peak_volume = parse_data_from_lines(lines)
        data.append((filepath.name, peak_flowrate, peak_volume))
    print_to_console(data, precision=precision)
    if save:
        write_to_csv(data, precision=precision, parent=filepaths[0].parent, filename='Unit Hydrograph Results.csv')

def parse_args() -> Tuple[List[str], int, bool]:
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        prog='Unit hydrograph parser',
        description='Parses unit hydrograph output files and converts data to csv format.')
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-s', '--save', action='store_true')
    parser.add_argument('-d', '--digits', type=int, default=2)
    args = parser.parse_args()

    # Grab all .out files in directories and sort by name
    files = []
    for path in args.paths:
        path = Path(path)
        if path.is_dir():
            files += list(path.glob('*.out'))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f'Cannot find item at {path}')
    files = sorted(files, key=natsort_key)

    # Restrict to single parent directory, since results are grouped into a single CSV file
    # TODO: support multiple simultaneous directories, if that behavior would be useful
    if len({file.parent for file in files}) > 1:
        print('Cannot parse output files from different directories; run UHParse separately for each target folder.')
        sys.exit(1)

    # Warning for csv files
    if any(path.endswith('.csv') for path in args.paths):
        warnings.warn('CSV file provided. Unexpected behavior will occur if attempting to parse the output of a previous UHParse execution.')

    return files, args.save, args.digits

def fix_cmd_arguments(argv):
    """Fix issues caused by CMD tab-completion with single-quoted paths ending in backslashes."""
    fixed_args = []
    for arg in argv: 
        if arg.startswith("'") and arg.endswith("\\"):  # Detect broken single-quoted paths
            arg = arg.rstrip("\\").rstrip("'")  # Remove the unwanted backslash and quote
        fixed_args.append(arg)
    return fixed_args

def natsort_key(s: str | Path) -> List[str | int]:
    """Key for natural sorting of filenames."""
    if isinstance(s, Path):
        s = s.name
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', s)]

def read_file(filepath: str) -> List[str]:
    """Read text file into list of lines."""
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    lines = [line.lower() for line in lines]
    return lines

def parse_data_from_lines(lines: List[str]) -> Tuple[float, float]:
    """Extract peak flow rate and volume from a list of file lines."""
    peak_flowrate = 0
    peak_volume = 0
    i0 = None
    i1 = None

    # Locate start and end of table
    for i, line in enumerate(lines):
        if TABLE_START_FLAG.lower() in line:
            i0 = i + TABLE_START_OFFSET
        if i0 is not None and i > i0:
            if TABLE_END_FLAG.lower() in line:
                i1 = i - TABLE_END_OFFSET
                break

    # Exit program if table was not identified from flags
    if i0 is None:
        print(f'Failed to find start of unit hydrograph table using the following flag:\n\t"{TABLE_START_FLAG}"')
        sys.exit(1)
    if i1 is None:
        print(f'Failed to find end of unit hydrograph table using provided flag:\n\t"{TABLE_END_FLAG}"')
        sys.exit(1)

    # Find peak flow rate and volume
    for i, line in enumerate(lines[i0:i1]):
        match = re.match(TABLE_PATTERN, line)
        if match is None or len(match.groups()) != 3:
            print(f'Failed to match text on line {i+i0} to the expected table format.\
                  This may indicate a malformed data entry or a case not yet handled by the script.')
        _, v_str, q_str = match.groups()
        peak_flowrate = max(peak_flowrate, float(q_str))
        peak_volume = max(peak_volume, float(v_str))

    return peak_flowrate, peak_volume

def print_to_console(data: List[Tuple[str, float, float]], precision: int = 2) -> None:
    """Print data to command line in a pretty table."""
    headers = ['Filename', 'Peak flowrate (CFS)', 'Peak volume (Ac.ft)']
    floatfmt = f'.{precision}F'
    tablefmt = 'github' #see "tabulate" docs for more formatting options
    print()
    print(tabulate(data, headers=headers, tablefmt=tablefmt, floatfmt=floatfmt))
    print()

def write_to_csv(data: List[Tuple[str, float, float]], parent: str | Path, filename: str, precision: int) -> None:
    """Output unit hydrograph data to .csv file."""
    headers = ['Filename', 'Peak flowrate (CFS)', 'Peak volume (Ac.ft)']
    filepath = Path(parent) / Path(filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for filename, peak_flowrate, peak_volume in data:
            writer.writerow([filename, f'{peak_flowrate:.{precision}F}', f'{peak_volume:.{precision}F}'])
    print(f'Saved data to {filepath}')

if __name__ == '__main__':
    main()
