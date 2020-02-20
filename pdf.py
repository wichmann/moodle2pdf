
import os
import logging
import tempfile
from itertools import chain

from bs4 import BeautifulSoup
from xhtml2pdf import document
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents

import moodle
from config import CONFIG, BORDER_HORIZONTAL, BORDER_VERTICAL, PAGE_HEIGHT, PAGE_WIDTH


logger = logging.getLogger('moodle2pdf.pdf')


def create_page_margins(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, CONFIG['pdf']['title'])
    canvas.drawRightString(PAGE_WIDTH-BORDER_HORIZONTAL,
                           BORDER_VERTICAL, "Seite {}".format(doc.page))
    canvas.restoreState()


def filter_html(bs):
    REMOVE_ATTRIBUTES = ['alt', 'rel', 'target', 'class', 'style']
    for tag in chain(bs.findAll('img'), bs.findAll('a'), bs.findAll('span')):
        tag.attrs = {key: value for key, value in tag.attrs.items()
                     if key not in REMOVE_ATTRIBUTES}


def extract_images(bs, directory):
    SCALING_FACTOR = 0.5
    image_list = []
    for tag in bs.findAll('img'):
        # get source link for images in entry
        image_file = moodle.download_image(tag['src'], directory)
        tag['src'] = image_file
        width = int(float(tag['width']) * SCALING_FACTOR)
        tag['width'] = str(width)
        height = int(float(tag['height']) * SCALING_FACTOR)
        tag['height'] = str(height)
        #tag['valign'] = 'super' # 'baseline', 'sub', 'super', 'top', 'text-top', 'middle', 'bottom', 'text-bottom', '0%', '2in'
        #tag.parent['spaceAfter'] = '2cm'
        tag.decompose()
        i = Image(image_file, width=width, height=height)
        i.vAlign = 'TOP'
        image_list.append(i)
    return image_list


def filter_for_xhtml2pdf(bs, directory):
    for tag in bs.findAll('img'):
        # get source link for images in entry
        image_file = moodle.download_image(tag['src'], directory)
        tag['src'] = image_file
    for tag in bs.findAll('br'):
        # remove all seperate line breaks and trust that all paragraphs are formatted with the <p> tag
        tag.decompose()


def substitute_lists(bs):
    for list_tag in bs.findAll('ul'):
        for tag in list_tag.findAll('li'):
            bullet = bs.new_tag('p', bulletFontName='Symbol')
            bullet.append(tag.text)
            tag.clear()
            tag.insert(0, bullet)
            tag.append('<br>')
            tag.name = 'p'
        #list_tag.name = 'div'
        print(list_tag)


def build_pdf_for_glossary(glossary_id, glossary_name, temp_dir):
    #question_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica-Bold', fontSize=11)
    #answer_paragraph_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=11, embeddedHyphenation=1, linkUnderline=1)
    part = []
    logger.info('Loading glossary: {} - {}'.format(glossary_id, glossary_name))
    # create heading
    heading =  document.pisaStory('<h1>{}</h1>'.format(glossary_name)).story
    part.extend(heading)
    # build paragraphs for questions
    for question, answer in moodle.get_entries_for_glossary(glossary_id, temp_dir):
        #
        part.extend(document.pisaStory('<h2>{}</h2>'.format(question)).story)
        bs = BeautifulSoup(answer, features='html.parser')
        filter_for_xhtml2pdf(bs, temp_dir)
        part.extend(document.pisaStory(str(bs)).story)
        #
        #bs = BeautifulSoup(answer, features='html5lib')  # 'lxml', 'html5lib'
        #filter_html(bs)
        #image_list = extract_images(bs, temp_dir)
        #substitute_lists(bs)
        #part.append(KeepTogether([Paragraph(question, question_paragraph_style),
        #                          Paragraph(str(bs), answer_paragraph_style),
        #                          Spacer(0, 0.25*cm), *image_list, Spacer(0, 0.75*cm)]))      
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
    document = SimpleDocTemplate(output_file, author=CONFIG['pdf']['author'], title=CONFIG['pdf']['title'])
    story = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for glossary_id, glossary_name in glossaries:
            story.extend(build_pdf_for_glossary(glossary_id, glossary_name, temp_dir))
        logger.info('Writing Moodle glossar to PDF file: {}.'.format(output_file))
        document.build(story, onFirstPage=create_page_margins, onLaterPages=create_page_margins)


def make_pdf_from_glossar_online(glossaries, combine_to_one_document=False):
    if combine_to_one_document:
        output_file = CONFIG['pdf']['default_output_filename']
        build_pdf_for_glossaries(glossaries, output_file)
    else:
        logger.error('NOT IMPLEMENTED YET!')
        #output_file = '{}.pdf'.format(f)
        #create_pdf_doc_online((f, ), output_file)
