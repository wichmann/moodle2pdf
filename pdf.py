
import logging
import tempfile
from itertools import chain

from bs4 import BeautifulSoup
from xhtml2pdf import document
from reportlab.platypus import SimpleDocTemplate, PageBreak, Image, HRFlowable

import moodle
from config import CONFIG, BORDER_HORIZONTAL, BORDER_VERTICAL, PAGE_WIDTH


logger = logging.getLogger('moodle2pdf.pdf')


def create_page_margins(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, CONFIG['pdf']['title'])
    canvas.drawRightString(PAGE_WIDTH - BORDER_HORIZONTAL,
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
        # tag['valign'] = 'super', 'baseline', 'sub', 'super', 'top', 'text-top', 'middle', 'bottom', 'text-bottom', '0%', '2in'
        # tag.parent['spaceAfter'] = '2cm'
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
    for tag in bs.find_all(type=True):
        # change all types in lists and enumerations to 'circle'
        tag['type'] = 'circle'


def substitute_lists(bs):
    for list_tag in bs.findAll('ul'):
        for tag in list_tag.findAll('li'):
            bullet = bs.new_tag('p', bulletFontName='Symbol')
            bullet.append(tag.text)
            tag.clear()
            tag.insert(0, bullet)
            tag.append('<br>')
            tag.name = 'p'
        print(list_tag)


def build_pdf_for_glossary(glossary_id, glossary_name, temp_dir):
    #
    # Some string include Unicode byte order marker ('\ufeff') to get the PDF
    # library to interpret them correctly. Without those markers non-ASCII
    # characters like German umlauts are not displyed correctly in the created
    # PDF file.
    #
    part = []
    logger.info('Loading glossary: {} - {}'.format(glossary_id, glossary_name))
    # create heading
    heading = document.pisaStory('\ufeff<h1>{} (Glossar)</h1>'.format(glossary_name)).story
    part.extend(heading)
    # build paragraphs for questions
    for question, answer in moodle.get_entries_for_glossary(glossary_id, temp_dir):
        part.extend(document.pisaStory('\ufeff<h2>{}</h2>'.format(question)).story)
        bs = BeautifulSoup(answer, features='html.parser')  # 'lxml', 'html5lib'
        filter_for_xhtml2pdf(bs, temp_dir)
        part.extend(document.pisaStory('\ufeff{}'.format(bs)).story)
        # insert divider between entries (see https://stackoverflow.com/a/36112136)
        part.append(HRFlowable(width='40%', thickness=2, color='darkgray'))
    # pop last divider
    part.pop()
    part.append(PageBreak())
    return part


def build_pdf_for_wiki(wiki_id, wiki_name, temp_dir):
    part = []
    logger.info('Loading wiki: {} - {}'.format(wiki_id, wiki_name))
    # create heading
    heading = document.pisaStory('\ufeff<h1>{} (Wiki)</h1>'.format(wiki_name)).story
    part.extend(heading)
    # build paragraphs for questions
    for page_id, page_name, page_content in moodle.get_subwiki_pages(wiki_id):
        part.extend(document.pisaStory('\ufeff<h2>{}</h2>'.format(page_name)).story)
        bs = BeautifulSoup(page_content, features='html.parser')
        # TODO: Handle if image is external link to another site.
        filter_for_xhtml2pdf(bs, temp_dir)
        part.extend(document.pisaStory('\ufeff{}'.format(bs)).story)
    part.append(PageBreak())
    return part


def build_pdf_for_database(database_id, database_name, temp_dir):
    part = []
    logger.info('Loading database: {} - {}'.format(database_id, database_name))
    # create heading
    heading = document.pisaStory('\ufeff<h1>{} (Datenbank)</h1>'.format(database_name)).story
    part.extend(heading)
    # build paragraphs for questions
    for entry in moodle.get_entries_for_database(database_id):
        entry_heading = document.pisaStory('\ufeff<h2>Eintrag: {}</h2>'.format(entry['id'])).story
        part.extend(entry_heading)
        for k, v in entry.items():
            # exclude file list
            if k != 'files' and k != 'id':
                if v in entry['files']:
                    image_file_name = moodle.download_image(entry['files'][v], temp_dir)
                    part.append(Image(image_file_name))  # , width=width, height=height)
                else:
                    part.extend(document.pisaStory('\ufeff<h3>{}</h3><p>{}</p>'.format(k, v)).story)
        # bs = BeautifulSoup(page_content, features='html.parser')
        # filter_for_xhtml2pdf(bs, temp_dir)
        # part.extend(document.pisaStory('\ufeff{}'.format(bs)).story)
    part.append(PageBreak())
    return part


def build_pdf_for_glossaries_and_wikis(glossaries, wikis, databases, output_file, callback=None):
    """
    Creates a PDF file from Moodle glossaries, wikis and databases accessed by Moodle Web Service.

    :param glossaries: list of glossaries to be exported, each entry containing a tuple of (at least) the id and name
                       for the glossary
    :param wikis: list of wikis to be exported, each entry containing a tuple of (at least) the id and name for a wiki
    :param databases: list of databases to be exported, each entry containing a tuple of (at least) the id and name for
                      the database
    :param output_file: file name for output PDF file
    """
    logger.info('Creating PDF file from Moodle Modules...')
    document = SimpleDocTemplate(output_file, author=CONFIG['pdf']['author'], title=CONFIG['pdf']['title'])
    story = []
    no = 0
    overall = len(glossaries) + len(wikis) + len(databases)
    if callback and callable(callback):
        callback(no, overall)
    with tempfile.TemporaryDirectory() as temp_dir:
        if glossaries:
            for glossary_id, glossary_name in glossaries:
                logger.info('Adding glossary no. {}: {}'.format(glossary_id, glossary_name))
                story.extend(build_pdf_for_glossary(glossary_id, glossary_name, temp_dir))
                no += 1
                if callback and callable(callback):
                    callback(no, overall)
        if wikis:
            for wiki_id, wiki_name, _, _, _, _ in wikis:
                logger.info('Adding wiki no. {}: {}'.format(wiki_id, wiki_name))
                story.extend(build_pdf_for_wiki(wiki_id, wiki_name, temp_dir))
                no += 1
                if callback and callable(callback):
                    callback(no, overall)
        if databases:
            for database_id, database_name, _, _ in databases:
                logger.info('Adding database no. {}: {}'.format(database_id, database_name))
                story.extend(build_pdf_for_database(database_id, database_name, temp_dir))
                no += 1
                if callback and callable(callback):
                    callback(no, overall)
        logger.info('Writing Moodle glossar to PDF file: {}.'.format(output_file))
        document.build(story, onFirstPage=create_page_margins, onLaterPages=create_page_margins)


def make_pdf_from_moodle(glossaries=None, wikis=None, databases=None, combine_to_one_document=False):
    if combine_to_one_document:
        output_file = CONFIG['pdf']['default_output_filename']
        build_pdf_for_glossaries_and_wikis(glossaries, wikis, databases, output_file)
    else:
        logger.error('NOT IMPLEMENTED YET!')
        # output_file = '{}.pdf'.format(f)
        # create_pdf_doc_online((f, ), output_file)
