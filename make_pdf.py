import argparse
from pathlib import Path

from pdf_utils import convert_to_pdf, open_pdf, get_filepaths


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Convert output files to PDF.")
    parser.add_argument('paths', type=str, nargs='*', default=[Path.cwd()], help='Path to one or more output files or directories. Currently supports WSPG .out and .wsw and CIVILD .out files.')
    parser.add_argument('-o', '--open', action='store_true', help='Opens PDFs using the default viewer after generation.')
    args = parser.parse_args()
    args.paths = [Path(p).resolve() for p in args.paths]
    return args


if __name__ == '__main__':
    # Get list of files to parse from command line arguments
    args = parse_args()
    filepaths = get_filepaths(args.paths)
    backup_dir = None

    for filepath in filepaths:
        # Convert to PDF, skipping on failure
        pdf_path, backup_dir = convert_to_pdf(filepath, backup_dir)
        if not pdf_path:
            continue
        
        # Open PDF if -o/--open option was provided
        if args.open:
            open_pdf(pdf_path)