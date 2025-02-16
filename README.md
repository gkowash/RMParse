# Rational Method Output Parser — v1.0.0
This script parses output files from a rational method hydrology model, extracts relevant flow data, and writes the processed information to CSV format. Additionally, if the "tabulate" package is available, it can print the extracted data to the command line in a formatted table.

To report bugs or request improvements, please open a Github issue or email Griffin at gkowash@gmail.com.

## Functionality
- Parses rational method output files for San Bernardino and Riverside counties.
- Writes node information, flow rate, and time concentration to a CSV file.
- Optionally prints the extracted data to the console in tabular format.

## Dependencies
- Python 3.12 or greater
- `tabulate` package
- `PyYAML` package

## Setup
Download or clone the [repository](https://github.com/gkowash/RMParse) and move it to the desired location on your machine. If downloaded, make sure to extract the resulting zip file.

For automatic setup, simply double-click the `install.bat` script in the `RMParse` directory. If the installer finishes successfully, the remainder of this section can be skipped.

For manual setup, first ensure that Python 3.12 or greater is installed on the machine. To check the current python installation, run:

```bat
python --version
```

Install the `tabulate` and `PyYAML` packages with the following commands, or using your preferred package manager:

```bat
pip install tabulate
pip install PyYAML
```

Finally, add the location of RMParse to the "Path" environment variable. This can be done as follows:
1. Open the Environment Variables menu, which can be acccessed from the Windows search bar.
2. Click the Environment Variables button at the bottom of the menu.
3. Select the Path field under "User variables" and click Edit.
4. Copy the path to the RMParse repository (on Windows 11, right-click and select "Copy as path").
5. In the Environment Variable editor, click New, paste in the copied path, and click OK.

Please contact Griffin if support for Linux is needed.

## Usage
Run the script from the command line with the following signature:

```bat
rmparse <file1> <file2> ... [-d DIGITS] [-p]
```

Arguments:
- `files`: One or more rational method output files to parse.
- `-d`, `--digits`: Number of decimal places for numeric output (default: 2).
- `-p`, `--print`: Print the extracted data in a table format if the "tabulate" package is available.

<!-- A set of input files for testing purposes is provided at `RMParse/test_files`. -->

The `rmparse.py` script can also be run directly using your preferred Python executable:

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