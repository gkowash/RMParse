# Rational Method Output Parser — v1.0.0
Created by Griffin Kowash, 7 February 2025

To report bugs or request improvements, please open a Github issue or email gkowash@gmail.com.

## Summary
This script parses output files from a rational method hydrology model, extracts relevant
flow data, and writes the processed information to CSV format. Additionally, if the 
"tabulate" package is available, it can print the extracted data to the command line in a formatted table.

## Functionality
- Reads a text-based hydrology model output file.
- Identifies and extracts flow rate and time of concentration (TOC) data.
- Supports different rational method command types, mapped via the `CommandCase` enum.
- Outputs extracted data as a CSV file.
- Optionally prints the extracted data in a tabular format.

## Dependencies
- Requires Python >=3.12
- Optional: The `tabulate` package for pretty-printing tables.

## Setup
Download or clone the repository at [insert repo URL] and move it to the desired location on your machine. Extract the zip file, if necessary.

Ensure that Python 3.12 or greater is installed on the machine. To check the current python installation, run:

```bat
python --version
```

Install the `tabulate` package using your preferred package manager. For most users, the following command is sufficient:

```bat
pip install tabulate
```

Finally, add the location of RMParse to the "Path" environment variable. This can be done as follows:
1. Open the Environment Variables menu, which can be acccessed from the Windows search bar.
2. Click the Environment Variables button at the bottom of the menu.
3. Select the Path field under "User variables" and click Edit.
4. Copy the path to the RMParse repository (on Windows 11, right-click and select "Copy as path").
5. In the Environment Variable editor, click New, paste in the copied path, and click OK.

Please contact Griffin if support for Linux is needed.

## Usage
Run the script from the command line with:

```bat
rmparse <file1> <file2> ... [-d DIGITS] [-p]
```

Arguments:
- `files`: One or more rational method output files to parse.
- `-d`, `--digits`: Number of decimal places for numeric output (default: 2).
- `-p`, `--print`: Print the extracted data in a table format if the "tabulate" package is available.

<!-- A set of input files for testing purposes is provided at `RMParse/test_files`. -->

If a non-default version of Python must be specified, the `rmparse.py` script can be run directly:

```bat
<path/to/python.exe> rmparse.py <file1> <file2> ... [-d DIGITS] [-p]
```

## Example output

```text
Wrote to csv file at .\test_files\testA.csv

| Nodes   |   Q (CFS) |   TC (min) |
|---------|-----------|------------|
| 101-102 |      4.26 |      17.00 |
| 102-102 |      6.65 |      17.00 |
| 102-103 |     14.69 |      22.19 |
| 103-104 |     17.94 |      23.70 |
```