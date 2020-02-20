#!/usr/bin/env python3

"""
Moodle2PDF loads data directly from Moodle glossaries and creates a PDF file
with the formatted entries.
"""

import sys
import getpass
import logging
import argparse
import logging.handlers

import pdf
import moodle
from config import CONFIG


logger = logging.getLogger('moodle2pdf')


def create_logger():
    global logger
    logger.setLevel(logging.DEBUG)
    log_to_file = logging.handlers.RotatingFileHandler(CONFIG['system']['log_filename'], maxBytes=262144, backupCount=5)
    log_to_file.setLevel(logging.DEBUG)
    logger.addHandler(log_to_file)
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.DEBUG)
    logger.addHandler(log_to_screen)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Converter for Moodle glossary files.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', '--link', help='link for a Moodle course')
    group.add_argument('-i', '--id', help='id of a Moodle course')
    parser.add_argument('-a', '--apart', action='store_false', help='create seperate PDF files for each glossary')
    parser.add_argument('-o', '--output', help='output PDF file to write glossaries to')
    parser.add_argument('-s', '--site', help='link to Moodle site', required=True)
    parser.add_argument('-u', '--username', help='username for Moodle site')
    parser.add_argument('-p', '--password', help='password for Moodle site')
    parser.add_argument('-g', '--glossary', help='include Glossary modules', action='store_false')
    parser.add_argument('-w', '--wiki', help='include Wiki modules', action='store_false')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    create_logger()
    args = parse_arguments()
    # handle username and password
    if args.username and args.password:
        username = args.username
        password = args.password
    else:
        username = input('Username: ')
        password = getpass.getpass(prompt='Password: ')
    # handle link/id of glossary
    if args.link:
        import re
        regex_glossary = r'.+mod\/glossary\/view\.php\?id=([0-9]{1,6})$'
        regex = r'(.+)course\/view\.php\?id=([0-9]{1,6})$'
        match = re.match(regex, args.link, re.MULTILINE)
        if match:
            site = match.group(1)
            course_id = match.group(2)
            logger.debug('Result of regex: {} {}'.format(site, course_id))
        else: 
            logger.error('Link not valid!')
            sys.exit()
    else:
        course_id = args.id
    logger.debug('Given course id was: {}'.format(course_id))
    # handle option combine, site URL and 
    if args.output:
        CONFIG['pdf']['default_output_filename'] = args.output
    if args.site:
        CONFIG['moodle']['url'] = args.site
        CONFIG['moodle']['token'] = moodle.get_token_for_user(username, password)
        pdf.make_pdf_from_glossar_online(moodle.get_glossaries_from_course(course_id), combine_to_one_document=args.apart)
    else:
        logger.error('Site URL not valid!')
