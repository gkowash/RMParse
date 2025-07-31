import os
import re
import time
import shutil
import subprocess
from pathlib import Path
from enum import Enum, auto
from typing import Tuple, List

from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

# Extensions used when searching for valid files in a directory
SUPPORTED_EXTENSIONS = ['.out', '.wsw']

# Load Courier New font on import
pdfmetrics.registerFont(TTFont('CourierNew', Path(__file__).parent / 'resources/fonts/cour.ttf'))


class FileCase(Enum):
    """Determines how each file should be formatted during PDF conversion."""
    WSPG_OUT = auto()
    WSPG_WSW = auto()
    CIVILD = auto()


def get_filepaths(paths: List[Path]) -> List[Path]:
    """Accept list of file/folder paths and return the files to be processed."""
    filepaths = []
    for path in paths:
        # Validate file extensions
        if path.is_file():
            if path.suffix in SUPPORTED_EXTENSIONS:
                filepaths.append(path)
            else:
                print(f'File does not have supported suffix: {path}')

        # Get all valid files from directory
        elif path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                filepaths.extend(path.glob(f'*{ext}'))
            
    # Handle case with no matching files
    if len(filepaths) == 0:
        print('Could not find any supported files at the following locations:')
        for path in paths:
            print('\t', path)
        sys.exit(1)

    # Retain only unique values + sort alphabetically
    filepaths = sorted(list(set(filepaths)))

    return filepaths


def get_file_case(filepath: Path) -> FileCase | None:
    """Determine whether a file is WSPG WSW, WSPG OUT, or CIVILD."""
    # Identify WSPG_WSW by suffix
    if filepath.suffix.lower() == '.wsw':
        return FileCase.WSPG_WSW
    
    # Load file contents for pattern matching
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()

    # Identify WSPG_OUT by header
    if re.search('W S P G W - CIVILDESIGN', text):
        return FileCase.WSPG_OUT
    
    # Identify CIVILD by header
    if re.search('CIVILCADD/CIVILDESIGN', text):
        return FileCase.CIVILD
    
    # Print message and return None on failure
    print(f'Failed to classify file as WSPG OUT, WSPG WSW, or CIVILD: {filepath}')
    return


def add_page_number(canvas, doc):
    """Add page number to footer of each page."""
    page = canvas.getPageNumber()
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(4.25 * inch, 0.70 * inch, str(page))


def open_pdf(filepath: Path) -> None:
    """Opens file using the default viewer."""
    subprocess.run(['start', filepath], shell=True, check=True)


def get_pdf_path(file_case: FileCase, input_path: Path, backup_dir: Path | None) -> Tuple[Path, Path | None]:
    """Construct PDF output path, avoiding overwrites using backups."""
    # Construct file path
    if file_case == FileCase.CIVILD:
        pdf_path = input_path.with_suffix('.pdf')
    elif file_case == FileCase.WSPG_OUT:
        pdf_path = input_path.with_name(f'{input_path.stem}OUT.pdf')
    elif file_case == FileCase.WSPG_WSW:
        pdf_path = input_path.with_name(f'{input_path.stem}WSW.pdf')
    else:
        raise ValueError(f'Invalid file case: {file_case}')
    
    # Handle overwrites by creating backup
    if pdf_path.exists():
        if not backup_dir:
            timestamp = time.strftime(r'%Y-%m-%d_%H%M%S')
            backup_dir = pdf_path.parent / f'PDF_OLD_{timestamp}'
            os.makedirs(backup_dir)
        shutil.copyfile(pdf_path, backup_dir / pdf_path.name)
        print(f'Backed up old file to {backup_dir / pdf_path.name}')

    return pdf_path, backup_dir


def convert_to_pdf(filepath: Path, backup_dir: Path | None) -> Tuple[Path | None, Path | None]:
    """Convert an output file to a PDF depending on the file type."""
    # Infer file type from name and/or contents
    file_case = get_file_case(filepath)
    if not file_case:
        return

    # Construct output filepath
    pdf_path, backup_dir = get_pdf_path(file_case, filepath, backup_dir)

    # Get PDF conversion function for the appropriate case
    case_functions = {
        FileCase.WSPG_OUT: wspg_out_to_pdf,
        FileCase.WSPG_WSW: wspg_wsw_to_pdf,
        FileCase.CIVILD: civild_to_pdf
    }
    pdf_func = case_functions[file_case]
    
    # Call corresponding PDF function
    try:
        pdf_func(filepath, pdf_path)
        print(f'Created PDF at {pdf_path}\n')
    except Exception as e:
        print(f'Failed to create PDF at {pdf_path}:\n{e}')
        return

    return pdf_path, backup_dir

def wspg_out_to_pdf(data_path: Path, pdf_path: Path) -> None:
    """Convert a WSPG .out file to a PDF."""
    # Create template
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(LETTER),
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
        )

    # Set paragraph style
    style = ParagraphStyle(
        name="Normal",
        fontName="CourierNew",
        fontSize=8,
        leading=9.6
    )

    # Create content
    with open(data_path, 'r', encoding='utf-8') as file:
        text = file.read()
        sections = text.split('\f') # Split by form feed character

    elements = []
    for i, section in enumerate(sections):
        if section in ('', '\n'):
            continue

        section_fmt = section.replace('\n', '<br/>').replace('\r', '<br/>').replace(' ', '&nbsp;').strip('<br/>')
        paragraph = Paragraph(section_fmt, style)
        elements.append(paragraph)

        if i < len(sections) - 1:  # Avoid adding a page break after the last section
            elements.append(PageBreak())

    # Construct PDF
    doc.build(elements)


def wspg_wsw_to_pdf(data_path: Path, pdf_path: Path) -> None:
    """Convert a WSPG .wsw file to a PDF."""
    # Create template
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(LETTER),
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
        )

    # Set paragraph style
    style = ParagraphStyle(
        name="Normal",
        fontName="CourierNew",
        fontSize=8,
        leading=9.6
    )

    # Create content
    with open(data_path, 'r', encoding='utf-8') as file:
        text = file.read().replace('\n', '<br/>').replace('\r', '<br/>').replace(' ', '&nbsp;')
    paragraph = Paragraph(text, style)

    # Costruct PDF
    doc.build([paragraph])


def civild_to_pdf(data_path: Path, pdf_path: Path) -> None:
    """Convert a CIVIL-D .out file to a PDF."""
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=LETTER,
        topMargin=0.65 * inch,
        bottomMargin=1.0 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )

    # Set paragraph styles
    header_style = ParagraphStyle(
        name="Header",
        fontName="CourierNew",
        fontSize=10,
        leading=11.3,
        alignment=TA_CENTER
    )

    body_style = ParagraphStyle(
        name="Text",
        fontName="CourierNew",
        fontSize=10,
        leading=11.3
    )

    # Create content
    with open(data_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # Process header
    header_end = [match.start() for match in re.finditer('\n', text)][4]
    header = text[:header_end]
    header = re.sub(r'^[^\S\r\n]+(?=\S)', '', header, flags=re.MULTILINE)
    header = header.replace('\n', '<br/>').replace('\r', '<br/>').replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')

    # Process body
    body = text[header_end:]
    body = re.sub(' +\n', '\n', body)
    body = body.replace('\n', '<br/>').replace('\r', '<br/>').replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')

    # Add elements to document
    header_paragraph = Paragraph(header, header_style)
    body_paragraph = Paragraph(body, body_style)
    doc.build([header_paragraph, body_paragraph], onFirstPage=add_page_number, onLaterPages=add_page_number)
