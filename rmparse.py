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
import re
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
    """Throw exception when flow rate and TC are not determined before the next header line is encountered."""
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code

class ParserState(Enum):
    """Cases for parser state."""
    SEARCHING = auto()
    PARSING_NODES = auto()
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
    def __init__(self, filepath: Path = None, data: dict = None):
        if filepath:
            self.load_from_file(filepath)
        elif data:
            self.load_from_dict(data)
        else:
            self.set_defaults()

    def load_from_file(self, filepath: str):
        """Load configuration from a YAML file."""
        with open(filepath, "r") as file:
            data = yaml.safe_load(file)
        self.load_from_dict(data)

    def load_from_dict(self, data: dict):
        """Load configuration from a provided dictionary, ensuring all match values are lists."""

        def normalize(value, suffix=""):
            """Ensure value is a list and apply transformations to each item."""
            return [(item.lower() + suffix) for item in (value if isinstance(value, list) else [value])]

        self.command_map = {CommandCase[key]: normalize(value) for key, value in data.get("commands", {}).items()}
        self.flowrate_map = {CommandCase[key]: normalize(value, suffix=' =') for key, value in data.get("flowrate", {}).items()}
        self.toc_map = {CommandCase[key]: normalize(value, suffix=' =') for key, value in data.get("time-of-concentration", {}).items()}
        self.new_section_text = data.get("new-section-text", {}).lower()
        self.node_text = data.get("node-text", {}).lower()
        self.confluence_summary_text = data.get("confluence-summary-text", {}).lower()

    def set_defaults(self):
        """Set default values if no configuration is provided."""
        self.command_map = {}
        self.flowrate_map = {}
        self.toc_map = {}
        self.new_section_text = ""
        self.confluence_summary_text = ""

def main() -> None:
    """Parse rational method output file, write data to csv, and print to console."""
    filepaths, precision, print_data = parse_args()
    for filepath in filepaths:
        data = process_file(filepath)
        csv_filepath = filepath.with_suffix('.csv')
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

def load_county_config(county: County, template_dir: str | Path) -> RMConfig:
    """Load template file corresponding to county name."""
    filename = county.value + '.yaml'
    filepath = Path(__file__).parent / template_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f'Could not find county template at {filepath}')
    config = RMConfig(filepath=filepath)
    return config

def process_file(filepath: Path, template_dir: Path = Path('templates')) -> List[Tuple[str, float, float]]:
    """Wrapper function to handle file reading, parsing, and status messages."""
    print(f'\nParsing {filepath.name}...')
    lines = read_file(filepath)
    county = next((c for c in County if c.value.lower() in " ".join(lines)), None)
    if county is None:
        raise ValueError("Could not determine county from file. Ensure it is listed in the County enum.")
    config = load_county_config(county, template_dir)
    data = parse_data_from_lines(lines, config)
    print('Finished parsing.')
    return data

def parse_data_from_lines(lines: List[str], config: RMConfig) -> List[Tuple[str, float, float]]:
    """Extract nodes, time of concentration, and flow rate from list of file lines."""
    state = ParserState.SEARCHING
    found_confluence_summary = False
    command = None
    nodes = None
    flowrate = None
    toc = None
    data = []

    for i, line in enumerate(lines):
        print(state)
        if config.new_section_text in line:
            print(f'{toc=}\n{flowrate=}')
            # Parse nodes on next line
            if state == ParserState.SEARCHING:
                state = ParserState.PARSING_NODES
            # Skip confluence if "Summary of stream data" is not found before next section header
            elif command in (CommandCase.CONFLUENCE_MAIN, CommandCase.CONFLUENCE_MINOR) and not found_confluence_summary:
                print('Skipping confluence')
                toc = None
                flowrate = None
                state = ParserState.PARSING_NODES
                continue
            # Throw error if neither of the above conditions are met
            else:
                raise InsufficientDataError(f'Failed to determine flow rate and time of concentration before next command header.\
                    \n\tFinal line: {i}\
                    \n\tCommand: {command}\
                    \n\tTC: {toc}\
                    \n\tFlow: {flowrate}')
            
        # Extract start and end node
        elif state == ParserState.PARSING_NODES:
            print(line)
            node1, node2 = parse_nodes(line)
            state = ParserState.PARSING_COMMAND

        # Match command header to expected cases
        elif state == ParserState.PARSING_COMMAND:
            command = get_command_case(line, config)
            if command is not None:
                nodes = format_nodes(node1, node2, command)
                state = ParserState.PARSING_STATS
            else:
                print('command is None - may indicate error') #TODO: characterize this case in detail

        # Read lines until flow rate and TC have been extracted
        elif state == ParserState.PARSING_STATS:
            found_confluence_summary = found_confluence_summary or (config.confluence_summary_text in line)
            if command in (CommandCase.CONFLUENCE_MAIN, CommandCase.CONFLUENCE_MINOR) and not found_confluence_summary:
                print('skipping stat read for confluence')
                continue  # for confluences, only read stats located after "Summary of stream data" line
            flowrate = flowrate or find_flowrate_in_line(line, config, command)
            toc = toc or find_toc_in_line(line, config, command)
            if flowrate is not None and toc is not None:
                state = ParserState.STORING_DATA

        # Save data and reset loop variables
        if state == ParserState.STORING_DATA:
            data.append((nodes, flowrate, toc))
            toc = None
            flowrate = None
            found_confluence_summary = False
            state = ParserState.SEARCHING

    return data

def parse_nodes(text: str) -> Tuple[str, str]:
    """Read line and return formatted node strings."""
    pattern = r'\.?0+$' #remove any trailing zeroes up to and including decimal point
    text_split = text.split()
    node1 = re.sub(pattern, '', text_split[3])
    node2 = re.sub(pattern, '', text_split[6])
    return node1, node2
    
def format_nodes(node1: str, node2: str, command: CommandCase) -> str:
    """Format a pair of nodes into a string."""
    if command in (CommandCase.CONFLUENCE_MAIN, CommandCase.CONFLUENCE_MINOR):
        return f'*{node1}-{node2}'
    else:
        return f'{node1}-{node2}'

def get_command_case(text: str, config: RMConfig) -> ParserState | None:
    """Parse command type, returning None if unspecified in text."""
    for command_case, flags in config.command_map.items():
        if any(flag in text for flag in flags):
            return command_case
    return None

def find_flowrate_in_line(line: str, config: RMConfig, command: CommandCase) -> float | None:
    """Extracts flowrate from a line if present."""
    if any(flag in line for flag in config.flowrate_map[command]):
        return get_flowrate(line)
    return None
    
def find_toc_in_line(line: str, config: RMConfig, command: CommandCase) -> float | None:
    """Extracts time of concentration from a line if present."""
    if any(flag in line for flag in config.toc_map[command]):
        return get_toc(line)
    return None

def get_flowrate(text: str) -> float:
    """Get flowrate from text."""
    flowrate_match = re.search(r'(\d+\.\d+)\(cfs\)', text)
    if not flowrate_match:
        print(f'Error - Failed to extract flow rate from line:\n\t{text}')
        sys.exit(1)
    flowrate = float(flowrate_match.group(1))
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
