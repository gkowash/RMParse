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

class County(Enum):
    """Supported counties for rational method parser."""
    SAN_BERNARDINO = 'San Bernardino'
    RIVERSIDE = 'Riverside'

class RMConfig:
    """Stores mappings and settings for Rational Method parsing."""
    def __init__(self, data=None):
        if data:
            self.load_from_dict(data)
        else:
            self.command_map = {}
            self.flowrate_map = {}
            self.toc_map = {}
            self.new_section_text = ""
            self.confluence_summary_texy = ""

    def load_from_file(self, filepath: str):
        """Load configuration from a YAML file."""
        with open(filepath, "r") as file:
            data = yaml.safe_load(file)
        self.load_from_dict(data)

    def load_from_dict(self, data: dict):
        """Load configuration from a provided dictionary."""
        self.command_map = {CommandCase[key]: value.lower() for key, value in data["commands"].items()}
        self.flowrate_map = {CommandCase[key]: value.lower() + " =" for key, value in data["flowrate"].items()}
        self.toc_map = {CommandCase[key]: value.lower() + " =" for key, value in data["time-of-concentration"].items()}
        self.new_section_text = data["new-section-text"].lower()
        self.confluence_summary_text = data["confluence-summary-text"].lower()

def main() -> None:
    """Parse rational method output file, write data to csv, and print to console."""
    filepaths, precision, print_data = parse_args()
    for filepath in filepaths:
        print(f'\nParsing {filepath.name}...')
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

def load_template_for_county(county: County, template_dir: str | Path) -> RMConfig:
    """Load template file corresponding to county name."""
    filename = county.value + '.yaml'
    filepath = Path(__file__).parent / template_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f'Could not find county template at {filepath}')
    config = RMConfig()
    config.load_from_file(filepath)
    return config

def parse_data_from_lines(lines: List[str], template_dir: str | Path = 'templates') -> List[Tuple[str, float, float]]:
    """Extract nodes, time of concentration, and flow rate from list of file lines."""
    state = ParserState.SEARCHING
    county = None
    config = None
    found_confluence_summary = False
    command = None
    nodes = None
    flowrate = None
    toc = None
    data = []

    for i, line in enumerate(lines):
        if county is None:
            county = next((county for county in County if county.value.lower() in line), None)
            if county is None:
                continue
            config = load_template_for_county(county, template_dir)

        if config.confluence_summary_text in line:
            found_confluence_summary = True

        if config.new_section_text in line:
            if state == ParserState.SEARCHING:
                node1, node2 = parse_nodes(line)
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
            command = get_command_case(line, config)
            if command is not None:
                nodes = format_nodes(node1, node2, command)
                state = ParserState.PARSING_STATS
            
        elif state == ParserState.PARSING_STATS:
            if config.flowrate_map[command] in line:
                flowrate = get_flowrate(line)
            elif config.toc_map[command] in line:
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

    print('Finished parsing.')

    return data

def parse_nodes(text: str) -> Tuple[int, int]:
    """Read line and return node numbers."""
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

def get_command_case(text: str, config: RMConfig) -> ParserState | None:
    """Parse command type, returning None if unspecified in text."""
    for command_case, flag in config.command_map.items():
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

def write_to_csv(data: List[Tuple[str, float, float]], filepath: str, precision: int, verbose: bool = True) -> None:
    """Output rational method data to .csv file."""
    headers = ['Nodes', 'Q', 'TC']  #TODO: add storm year as suffix to Q
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for node_str, toc, flowrate in data:
            writer.writerow([node_str, f'{toc:.{precision}F}', f'{flowrate:.{precision}F}'])
    if verbose:
        print(f'Saved data to {filepath}')

if __name__ == '__main__':
    main()
