"""
Rational Method Output Parser

This script parses output files from a rational method hydrology model, extracts relevant
flow data, and writes the processed information to CSV format. Additionally, if the 
"tabulate" package is available, it can print the extracted data in a formatted table.

Run the script from the command line with:
    python rmparse.py <file1> <file2> ... [-d DIGITS] [-p]

To use the more concise "rmparse" command, add the RMParse repository to the Path environment
variable.
"""

import sys
import os
import csv
import argparse
import warnings
from pathlib import Path
from enum import Enum, auto
from typing import Tuple, List

import yaml

try:
    from tabulate import tabulate
    PRINT_DATA = True
except Exception as e:
    PRINT_DATA = False
    print('Unable to print data; failed to import package "tabulate".')

class InsufficientDataError(Exception):
    """Throw exception when flow rate and TOC are not determined before the next header line is encountered."""
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code

class ParserState(Enum):
    """Cases for parser state."""
    SEARCHING = auto()
    PARSING_COMMAND = auto()
    PARSING_STATS = auto()
    STORING_DATA = auto()

class CommandCase(Enum):
    """Cases for rational method commands."""
    INITIAL_AREA = "INITIAL_AREA"
    STREET_FLOW = "STREET_FLOW"
    STREET_INLET = "STREET_INLET"
    SUBAREA_ADDITION = "SUBAREA_ADDITION"
    PIPEFLOW_PROGRAM = "PIPEFLOW_PROGRAM"
    PIPEFLOW_USER = "PIPEFLOW_USER"
    CHANNEL_IMPROVED = "CHANNEL_IMPROVED"
    CHANNEL_IRREGULAR = "CHANNEL_IRREGULAR"
    USER = "USER"
    CONFLUENCE_MINOR = "CONFLUENCE_MINOR"
    CONFLUENCE_MAIN = "CONFLUENCE_MAIN"

# class Counties(Enum):
#     """Supported counties with YAML template files."""
#     SAN_BERNARDINO = "San Bernardino"
#     RIVERSIDE = "Riverside"

COUNTIES = ('San Bernardino', 'Riverside')
TEMPLATE_DIR = 'templates'
# COMMAND_MAP = {
#     CommandCase.INITIAL_AREA: "INITIAL AREA EVALUATION",
#     CommandCase.STREET_FLOW: "STREET FLOW TRAVEL TIME",
#     CommandCase.STREET_INLET: "(command flag undefined)",
#     CommandCase.SUBAREA_ADDITION: "SUBAREA FLOW ADDITION",
#     CommandCase.PIPEFLOW_PROGRAM: "PIPEFLOW TRAVEL TIME (Program estimated size)",
#     CommandCase.PIPEFLOW_USER: "PIPEFLOW TRAVEL TIME (User specified size)",
#     CommandCase.CHANNEL_IMPROVED: "IMPROVED CHANNEL TRAVEL TIME",
#     CommandCase.CHANNEL_IRREGULAR: "IRREGULAR CHANNEL FLOW TRAVEL TIME",
#     CommandCase.USER: "USER DEFINED FLOW INFORMATION AT A POINT",
#     CommandCase.CONFLUENCE_MINOR: "CONFLUENCE OF MINOR STREAMS",
#     CommandCase.CONFLUENCE_MAIN: "CONFLUENCE OF MAIN STREAMS"
# }

# FLOWRATE_MAP = {
#     CommandCase.INITIAL_AREA: "Subarea runoff",
#     CommandCase.STREET_FLOW: "Total runoff",
#     CommandCase.STREET_INLET: "(command flag undefined)",
#     CommandCase.SUBAREA_ADDITION: 'Total runoff',
#     CommandCase.PIPEFLOW_PROGRAM: 'Required pipe flow',
#     CommandCase.PIPEFLOW_USER: 'Required pipe flow',
#     CommandCase.CHANNEL_IMPROVED: 'Total runoff',
#     CommandCase.CHANNEL_IRREGULAR: 'Total runoff',
#     CommandCase.USER: 'Total runoff',
#     CommandCase.CONFLUENCE_MINOR: 'Total flow rate',
#     CommandCase.CONFLUENCE_MAIN: 'Total flow rate'
# }

# TOC_MAP = {
#     CommandCase.INITIAL_AREA: "Initial area time of concentration =",
#     CommandCase.STREET_FLOW: "TC =",
#     CommandCase.STREET_INLET: "(command flag undefined)",
#     CommandCase.SUBAREA_ADDITION: 'Time of concentration =',
#     CommandCase.PIPEFLOW_PROGRAM: 'Time of concentration (TC) =',
#     CommandCase.PIPEFLOW_USER: 'Time of concentration (TC) =',
#     CommandCase.CHANNEL_IMPROVED: 'Time of concentration =',
#     CommandCase.CHANNEL_IRREGULAR: 'Time of concentration =',
#     CommandCase.USER: 'TC =',
#     CommandCase.CONFLUENCE_MINOR: 'Time of concentration =',
#     CommandCase.CONFLUENCE_MAIN: 'Time of concentration ='
# }

# NEW_SECTION_TEXT = 'Process from Point/Station'
# CONFLUENCE_SUMMARY_TEXT = 'Summary of stream data'

COMMAND_MAP = None
FLOWRATE_MAP = None
TOC_MAP = None
NEW_SECTION_TEXT = None
CONFLUENCE_SUMMARY_TEXT = None

def main() -> None:
    """Parse rational method output file, write data to csv, and print to console."""
    filepaths, precision, print_data = parse_args()
    for filepath in filepaths:
        lines = read_file(filepath)
        data = parse_data_from_lines(lines)
        csv_filepath = get_csv_filepath(filepath)
        write_to_csv(data, precision=precision, filepath=csv_filepath)
        if print_data and PRINT_DATA:
            print_to_console(data, precision=precision)

def parse_args() -> Tuple[List[str], int, bool]:
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        prog='Rational method parser',
        description='Parses rational method output files and converts data to csv format.')
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-d', '--digits', type=int, default=2)
    parser.add_argument('-p', '--print', action='store_true')
    args = parser.parse_args()

    # Grab all .out files in directories
    files = []
    for path in args.paths:
        path = Path(path)
        if path.is_dir():
            files += list(path.glob("*.out"))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f'Cannot find item at {path}')
   
    # Warning for csv files
    if any(path.endswith('.csv') for path in args.paths):
        warnings.warn('CSV file provided. Unexpected behavior will occur if attempting to parse the output of a previous RMParse execution.')

    return files, args.digits, args.print

def read_file(filepath: str) -> List[str]:
    """Read text file into list of lines."""
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    lines = [line.lower() for line in lines]
    return lines

def load_template_file(filepath: str) -> None:
    """Populate county-specific text mappings from YAML file."""
    global COMMAND_MAP, FLOWRATE_MAP, TOC_MAP, NEW_SECTION_TEXT, CONFLUENCE_SUMMARY_TEXT
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)
    COMMAND_MAP = {CommandCase[key]: value.lower() for key, value in data['commands'].items()}
    FLOWRATE_MAP = {CommandCase[key]: value.lower() + ' =' for key, value in data['flowrate'].items()}
    TOC_MAP = {CommandCase[key]: value.lower() + ' =' for key, value in data['time-of-concentration'].items()}
    NEW_SECTION_TEXT = data['new-section-text'].lower()
    CONFLUENCE_SUMMARY_TEXT = data['confluence-summary-text'].lower()

def load_template_for_county(county: str) -> None:
    """Load template file corresponding to county name."""
    filename = county + '.yaml'
    filepath = Path(__file__).parent / TEMPLATE_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f'Could not find county template at {filepath}')
    load_template_file(filepath)

def parse_data_from_lines(lines: List[str]) -> List[Tuple[str, float, float]]:
    """Extract nodes, time of concentration, and flow rate from list of file lines."""
    state = ParserState.SEARCHING
    county = None
    found_confluence_summary = False
    command = None
    nodes = None
    flowrate = None
    toc = None
    data = []

    for i, line in enumerate(lines):
        if county is None:
            county = next((county for county in COUNTIES if county.lower() in line), None)
            if county is None:
                continue
            load_template_for_county(county)

        if CONFLUENCE_SUMMARY_TEXT in line:
            found_confluence_summary = True

        if NEW_SECTION_TEXT in line:
            if state == ParserState.SEARCHING:
                node1, node2 = get_nodes(line)
                state = ParserState.PARSING_COMMAND
            # If a confluence entry is missing "Summary of stream data", we don't expect to find flow data
            elif command in (CommandCase.CONFLUENCE_MAIN, CommandCase.CONFLUENCE_MINOR) and not found_confluence_summary:
                state = ParserState.SEARCHING
                continue
            else:
                raise InsufficientDataError(f'Failed to determine flow rate and time of concentration before next command header.\
                    \n\tFinal line: {i}\
                    \n\tCommand: {command}\
                    \n\tTOC: {toc}\
                    \n\tFlow: {flowrate}')
            
        elif state == ParserState.PARSING_COMMAND:
            command = get_command_case(line)
            if command is not None:
                nodes = format_nodes(node1, node2, command)
                state = ParserState.PARSING_STATS
            
        elif state == ParserState.PARSING_STATS:
            if FLOWRATE_MAP[command] in line:
                flowrate = get_flowrate(line)
            elif TOC_MAP[command] in line:
                toc = get_toc(line)
            if flowrate is not None and toc is not None:
                state = ParserState.STORING_DATA
        
        if state == ParserState.STORING_DATA:
            data.append((nodes, flowrate, toc))
            toc = None
            flowrate = None
            found_confluence_summary = False
            state = ParserState.SEARCHING

    if county is None:
        print('Failed to identify county from output file. Ensure that the county is specified in the COUNTIES variable and has a corresponding YAML template.')
        sys.exit(1)

    return data

def get_nodes(text: str) -> str:
    """Parse text and return formatted note string."""
    node1, node2 = parse_nodes(text)
    return node1, node2

def parse_nodes(text: str) -> Tuple[int, int]:
    """Read node numbers and return formatted string."""
    text_split = text.split()
    node1 = int(float(text_split[3]))
    node2 = int(float(text_split[6]))
    return node1, node2
    
def format_nodes(node1: int, node2: int, command: CommandCase) -> str:
    """Format a pair of nodes into a string."""
    if command in (CommandCase.CONFLUENCE_MAIN, CommandCase.CONFLUENCE_MINOR):
        return f'*{node1}-{node2}'
    else:
        return f'{node1}-{node2}'

def get_command_case(text: str) -> ParserState | None:
    """Parse command type, returning None if unspecified in text."""
    for command_case, flag in COMMAND_MAP.items():
        if flag in text:
            return command_case
    return None

def get_flowrate(text: str) -> float:
    """Get flowrate from text."""
    flowrate_str = text.strip().split()[-1]
    flowrate = float(flowrate_str.split('(')[0]) #remove (CFS) suffix
    return flowrate

def get_toc(text: str) -> float:
    """Get time of concentration from text."""
    return float(text.strip().split()[-2])

def get_csv_filepath(filepath: str) -> str:
    """Generate csv filepath with same name and location as source."""
    basename, _ = os.path.splitext(filepath)
    return basename + '.csv'

def print_to_console(data: List[Tuple[str, float, float]], precision: int = 2) -> None:
    """Print data to command line in a pretty table."""
    headers = ['Nodes', 'Q (CFS)', 'TC (min)'] #TODO: move outside of print_data and write_to_csv
    floatfmt = f'.{precision}F'
    tablefmt = 'github' #see "tabulate" docs for more formatting options
    print()
    print(tabulate(data, headers=headers, tablefmt=tablefmt, floatfmt=floatfmt))
    print()

def write_to_csv(data: List[Tuple[str, float, float]], filepath: str, precision: int) -> None:
    """Output rational method data to .csv file."""
    headers = ['Nodes', 'Q', 'TC']  #TODO: add storm year as suffix to Q
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for node_str, toc, flowrate in data:
            writer.writerow([node_str, f'{toc:.{precision}F}', f'{flowrate:.{precision}F}'])
    print(f'Extracted data to {filepath}')

if __name__ == '__main__':
    main()
