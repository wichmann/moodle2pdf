#!/usr/bin/env python3

"""
FAQ Export:

https://moodle.nibis.de/bbs_osb/pluginfile.php/288/mod_glossary/export/0/0/export.xml?forcedownload=1
https://moodle.nibis.de/bbs_osb/pluginfile.php/289/mod_glossary/export/0/0/export.xml?forcedownload=1
https://moodle.nibis.de/bbs_osb/pluginfile.php/14179/mod_glossary/export/0/0/export.xml?forcedownload=1
https://moodle.nibis.de/bbs_osb/pluginfile.php/14389/mod_glossary/export/0/0/export.xml?forcedownload=1
https://moodle.nibis.de/bbs_osb/pluginfile.php/21393/mod_glossary/export/0/0/export.xml?forcedownload=1

"""

import sys
import json
import datetime
import urllib.parse
import logging
import logging.handlers
from itertools import chain

import requests
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


KEY = ''
URL = ''
ENDPOINT = 'webservice/rest/server.php'


def rest_api_parameters(in_args, prefix='', out_dict=None):
    """Transform dictionary/array structure to a flat dictionary, with key names
    defining the structure.

    Source: https://github.com/mrcinv/moodle_api.py/blob/master/moodle_api.py

    Example usage:
    >>> rest_api_parameters({'courses':[{'id':1,'name': 'course1'}]})
    {'courses[0][id]':1,
     'courses[0][name]':'course1'}
    """
    if out_dict == None:
        out_dict = {}
    if not type(in_args) in (list, dict):
        out_dict[prefix] = in_args
        return out_dict
    if prefix == '':
        prefix = prefix + '{0}'
    else:
        prefix = prefix + '[{0}]'
    if type(in_args) == list:
        for idx, item in enumerate(in_args):
            rest_api_parameters(item, prefix.format(idx), out_dict)
    elif type(in_args) == dict:
        for key, item in in_args.items():
            rest_api_parameters(item, prefix.format(key), out_dict)
    return out_dict


def call(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.

    Source: https://github.com/mrcinv/moodle_api.py/blob/master/moodle_api.py

    Example:
    >>> call_mdl_function('core_course_update_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update(
        {"wstoken": KEY, 'moodlewsrestformat': 'json', "wsfunction": fname})
    response = requests.post(urllib.parse.urljoin(URL, ENDPOINT), parameters)
    response = response.json()
    if type(response) == dict and response.get('exception'):
        raise SystemError("Error calling Moodle API\n", response)
    return response


def download_image(link):
    try:
        filter_html.counter += 1
    except AttributeError:
        filter_html.counter = 1
    # , 'moodlewsrestformat': 'json'} #, "wsfunction": fname}
    parameters = {"token": KEY}
    logger.info('Loading image from {}'.format(link))
    response = requests.post(link, parameters)
    image_file_name_on_disk = 'image{}.png'.format(filter_html.counter)
    with open(image_file_name_on_disk, 'wb') as image_on_disk:
        image_on_disk.write(response.content)
    return image_file_name_on_disk


def get_glossaries_from_course(courseid):
    id_list = []
    response = call('mod_glossary_get_glossaries_by_courses',
                    courseids=[courseid])
    for g in response['glossaries']:
        id_list.append((g['id'], g['name']))
    return id_list


def get_entries_for_glossary(glossary_id):
    entries = call('mod_glossary_get_entries_by_letter',
                   id=glossary_id, letter='ALL', limit=100)
    with open('loaded_data_{}.xml'.format(glossary_id), 'w') as f:
        f.write(str(entries))
    no = entries['count']
    for e in entries['entries']:
        yield (e['concept'], e['definition'])


def create_page_margins(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, TITLE)
    canvas.drawRightString(PAGE_WIDTH-BORDER_HORIZONTAL,
                           BORDER_VERTICAL, "Seite {}".format(doc.page))
    canvas.restoreState()


def filter_html(text):
    REMOVE_ATTRIBUTES = ['alt', 'rel', 'target', 'class', 'style']
    # src is used for giving URLs for images!!!
    bs = BeautifulSoup(text, features='html5lib')  # 'lxml')#'html5lib')
    for tag in bs.findAll('img'):
        print(tag)
        download_link = tag['src']
        tag['src'] = download_image(download_link)
        tag['width'] = str(int(tag['width']) / 2)
        tag['height'] = str(int(tag['height']) / 2)
        # width="0.57in" height="50%%"
    for tag in chain(bs.findAll('img'), bs.findAll('a'), bs.findAll('span')):
        tag.attrs = {key: value for key, value in tag.attrs.items()
                     if key not in REMOVE_ATTRIBUTES}
    return str(bs)


def build_pdf_for_glossary(glossary_id, glossary_name):
    heading_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=16)
    question_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica-Bold', fontSize=11)
    answer_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=11, embeddedHyphenation=1, linkUnderline=1)
    part = []
    logger.info('Loading glossary: {} - {}'.format(glossary_id, glossary_name))
    # create heading
    heading = glossary_name
    part.append(Paragraph(heading, heading_paragraph_style))
    part.append(Spacer(0, 1.0*cm))
    # build paragraphs for questions
    for question, answer in get_entries_for_glossary(glossary_id):
        answer = filter_html(answer)
        part.append(KeepTogether([Paragraph(question, question_paragraph_style),
                                    Paragraph(answer, answer_paragraph_style),
                                    Spacer(0, 0.75*cm)]))
    part.append(PageBreak())
    return part


def build_pdf_for_glossaries(glossaries, output_file):
    """
    Creates a PDF file from Moodle glossaries accessed by Moodle Web Service.

    :param glossaries: tuple of id and name for a single glossary or a list of
                       tuples for all glossaries
    :param output_file: file name for output PDF file
    """
    logger.info('Creating PDF file from Moodle Glossar...')
    # define styles for page elements
    centered = ParagraphStyle(name='centered', fontSize=30, leading=16, alignment=1, spaceAfter=20)
    h1 = ParagraphStyle(name='Heading1', fontSize=14, leading=16)
    h2 = ParagraphStyle(name='Heading2', fontSize=12, leading=14)
    # set title for document
    global TITLE
    # if len(glossar_files) == 1:
    #    TITLE = os.path.splitext(os.path.basename(glossar_files[0]))[0]
    doc = SimpleDocTemplate(output_file, author=AUTHOR, title=TITLE)
    story = []
    # build document
    for glossary_id, glossary_name in glossaries:
        story.extend(build_pdf_for_glossary(glossary_id, glossary_name))
    logger.info('Writing Moodle glossar to PDF file: {}.'.format(output_file))
    doc.build(story, onFirstPage=create_page_margins, onLaterPages=create_page_margins)


def create_logger():
    global logger
    logger.setLevel(logging.DEBUG)
    log_to_file = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=262144, backupCount=5)
    log_to_file.setLevel(logging.DEBUG)
    logger.addHandler(log_to_file)
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.INFO)
    logger.addHandler(log_to_screen)


def make_pdf_from_glossar_online(glossaries, combine_to_one_document=False):
    if combine_to_one_document:
        output_file = DEFAULT_OUTPUT_FILENAME
        build_pdf_for_glossaries(glossaries, output_file)
    else:
        logger.error('NOT IMPLEMENTED YET!')
        #output_file = '{}.pdf'.format(f)
        #create_pdf_doc_online((f, ), output_file)


if __name__ == '__main__':
    create_logger()
    #args = parse_arguments()
    course_id = 7
    make_pdf_from_glossar_online(get_glossaries_from_course(
        course_id), combine_to_one_document=True)
