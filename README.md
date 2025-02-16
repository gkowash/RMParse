# Rational Method Output Parser — v1.0.0
This script parses output files from a rational method hydrology model, extracts relevant flow data, and writes the processed information to CSV format. Additionally, if the "tabulate" package is available, it can print the extracted data to the command line in a formatted table.

To report bugs or request improvements, please open a Github issue or email Griffin at gkowash@gmail.com.

## Functionality
- Identifies and extracts flow rate and time of concentration data from rational method output files.
- Outputs extracted data as a CSV file.
- Optionally prints the extracted data in a tabular format.

## Dependencies
- Requires Python 3.12 or greater
- Optional: The `tabulate` package for pretty-printing tables.

## Setup
Download or clone the [repository](https://github.com/gkowash/RMParse) and move it to the desired location on your machine. If downloading directly, make sure to extract the resulting zip file.

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

```text
<path/to/python.exe> rmparse.py <file1> <file2> ... [-d DIGITS] [-p]
```

## Examples
The following command will parse a rational method output file named `example.out`, save the data to a CSV file with the same name, and print a table to the console:
```text
rmparse example.out --print
```
Or equivalently:
```text
rmparse example.out -p
```

An example terminal output is shown below for reference.
```text
Wrote to csv file at example.csv

| Nodes   |   Q (CFS) |   TC (min) |
|---------|-----------|------------|
| 101-102 |      4.26 |      17.00 |
| 102-102 |      6.65 |      17.00 |
| 102-103 |     14.69 |      22.19 |
| 103-104 |     17.94 |      23.70 |
```

To simulateneously parse two output files located in a directory named `data`, and format the results to one decimal place:
```text
rmparse data/example1.out data/example2.out --digits 1
```
Or equivalently:
```text
rmparse data/example1.out data/example2.out -d 1
```