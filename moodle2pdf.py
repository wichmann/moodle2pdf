#!/usr/bin/env python3

"""
Creates a PDF file from Moodle glossar data exported into XML files. All XML
files in the local directory will be converted. You can select if each XML file
should be converted into a separate PDF or if all data from all files should be
converted into one big PDF file.

Author: Christian Wichmann
Date: 2018-04-27
"""

import os
import sys
import argparse
import datetime
import logging
import logging.handlers

from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents


logger = logging.getLogger('moodle2pdf')


LOG_FILENAME = 'moodle2pdf.log'
DEFAULT_OUTPUT_FILENAME = 'FAQ.pdf'
PAGE_WIDTH, PAGE_HEIGHT = A4
BORDER_HORIZONTAL = 2.0*cm
BORDER_VERTICAL = 1.5*cm
TODAY = datetime.datetime.today().strftime('%d.%m.%Y')
AUTHOR = 'Christian Wichmann'
TITLE = 'Häufig gestellte Fragen - Logodidact und Moodle'


def create_page_margins(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, TITLE)
    canvas.drawRightString(PAGE_WIDTH-BORDER_HORIZONTAL, BORDER_VERTICAL, "Seite {}".format(doc.page))
    canvas.restoreState()


def create_pdf_doc(glossar_files, output_file):
    """
    Creates a PDF file from Moodle glossar that were exported into the XML
    file format.
    
    :param glossar_files: tuple of file names or string containing a single
                          file name, that file should contain the glossars
                          in Moodle's XML format.
    :param output_file: file name for output PDF file
    """
    logger.info('Creating PDF file from Moodle Glossar...')
    # define styles for page elements
    heading_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=16) 
    question_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica-Bold', fontSize=11) 
    answer_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=11)
    centered = ParagraphStyle(name='centered', fontSize=30, leading=16, alignment=1, spaceAfter=20)
    h1 = ParagraphStyle(name='Heading1', fontSize=14, leading=16)
    h2 = ParagraphStyle(name='Heading2', fontSize=12, leading=14)
    # set title for document
    global TITLE
    if len(glossar_files) == 1:
        TITLE = os.path.splitext(os.path.basename(glossar_files[0]))[0]
    doc = SimpleDocTemplate(output_file, author=AUTHOR, title=TITLE)
    story = []
    # build document
    for f in glossar_files:
        with open(f, 'r') as glossar_data:
            bs = BeautifulSoup(glossar_data.read(), features="xml")
        # create heading
        heading = str(bs.find('NAME').get_text())
        story.append(Paragraph(heading, heading_paragraph_style))
        # TODO: Set bookmark for heading in PDF file.
        story.append(Spacer(0, 1.0*cm))
        # build paragraphs for questions
        for e in bs.find('ENTRIES').find_all('ENTRY'):
            question = str(e.find('CONCEPT').get_text()).replace('<br>', '')
            answer = str(e.find('DEFINITION').get_text()).replace('<br>', '')
            story.append(KeepTogether([Paragraph(question, question_paragraph_style),
                                    Paragraph(answer, answer_paragraph_style),
                                    Spacer(0, 0.75*cm)]))
            # TODO: Set bookmark for question in PDF file.
        story.append(PageBreak())
    logger.info('Writing Moodle glossar to PDF file: {}.'.format(output_file))
    doc.build(story, onFirstPage=create_page_margins, onLaterPages=create_page_margins)


def create_logger():
    global logger
    logger.setLevel(logging.DEBUG)
    log_to_file = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=262144, backupCount=5)
    log_to_file.setLevel(logging.DEBUG)
    logger.addHandler(log_to_file)
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.INFO)
    logger.addHandler(log_to_screen)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Converter for Moodle glossar files.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--all', action='store_true',
                       help='convert all XML files in directory')
    group.add_argument('-f', '--files', action='store', nargs='+',
                       help='provide a list of files to convert')
    parser.add_argument('-c', '--combine', action='store_true',
                        help='combine all glossar data into one PDF file')
    args = parser.parse_args()
    return args


def make_pdf_from_glossar(filelist, combine_to_one_document=False):
    if combine_to_one_document:
        output_file = DEFAULT_OUTPUT_FILENAME
        create_pdf_doc(filelist, output_file)
    else:
        for f in filelist:
            output_file = '{}.pdf'.format(f)
            create_pdf_doc((f, ), output_file)


if __name__ == '__main__':
    create_logger()
    args = parse_arguments()
    if args.all:
        filelist = [file for file in os.listdir(".") if file.endswith(".xml")]
        logger.info('Found these XML glossar files: {}.'.format(filelist))
    elif args.files:
        filelist = args.files
        logger.info('Converting only these XML glossar files: {}.'.format(filelist))
    make_pdf_from_glossar(filelist, combine_to_one_document=args.combine)
