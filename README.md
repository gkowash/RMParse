# Hydrology Output Parser — v1.0.0
This package provides tools for extracting data from rational method and unit hydrograph output files.

To report bugs or request improvements, please open a Github issue or email Griffin at gkowash@gmail.com.

## Functionality
`RMParse`
- Parses rational method output files for San Bernardino and Riverside counties
- Extracts node information, flow rate, and time of concentration
- Writes results to a CSV file
- Optionally prints results to the console

`UHParse`
- Parses unit hydrograph output files for San Bernardino and Riverside counties
- Extracts peak flow rate and peak volume
- Prints results to the console
- Optionally writes results to a CSV file

## Dependencies
- Python 3.12 or greater
- `tabulate` package
- `PyYAML` package

## Setup
Download or clone the [repository](https://github.com/gkowash/RMParse) and move it to the desired location on your machine. If downloaded, make sure to extract the resulting zip file.

For automatic setup, simply double-click the `install.bat` script in the `RMParse` directory. If the installer finishes successfully, the remainder of this section can be skipped; otherwise, follow the manual instructions and troubleshoot as needed.

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
### RMParse
Run the rational method output parser from the command line with the following signature:

```bat
rmparse <path1> <path2> ... [-d DIGITS] [-p]
```

Arguments:
- `paths`: One or more files or directories containing rational method ouput data.
- `-d`, `--digits`: If provided, sets the number of decimal places for numeric output (default: 2).
- `-p`, `--print`: If provided, prints the extracted data to the console.

The `rmparse.py` script can also be run directly using your preferred Python executable:

```text
<path/to/python.exe> rmparse.py <path1> <path2> ... [-d DIGITS] [-p]
```

### UHParse
Run the unit hydrograph output parser from the command line with the following signature:

```bat
uhparse <path1> <path2> ... [-d DIGITS] [-s]
```

Arguments:
- `paths`: Paths to files or a directory containing unit hydrograph output data. All files must be located in the same directory.
- `-d`, `--digits`: If provided, sets the number of decimal places for numeric output (default: 2).
- `-s`, `--save`: If provided, saves the combined data from all output files in CSV format.

## Examples
### RMParse

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
Saved data to example.csv

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

### UHParse
The following command will parse all unit hydrograph output files in a directory named `unit_hydrograph`, save the data to a CSV file, and print a table to the console:
```text
uhparse unit_hydrograph --save
```
Or equivalently:
```text
uhparse unit_hydrograph -s
```

An example terminal output is shown below for reference.
```text
Parsing file UH1.out
Parsing file UH2.out

| Filename       |   Peak flowrate (CFS) |   Peak volume (Ac.ft) |
|----------------|-----------------------|-----------------------|
| UH1.out        |                 26.18 |                  5.15 |
| UH2.out        |                  3.95 |                  0.66 |
```

To view the table without writing to a CSV file, simply omit the `--save`/`-s` argument.