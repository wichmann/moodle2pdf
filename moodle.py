
import os
import logging
import urllib.parse

import requests

from config import CONFIG


logger = logging.getLogger('moodle2pdf.moodle')


############################## General functions ########################################

def rest_api_parameters(in_args, prefix='', out_dict=None):
    """Transform dictionary/array structure to a flat dictionary, with key names
    defining the structure.

    Source: https://github.com/mrcinv/moodle_api.py/blob/master/moodle_api.py

    Example usage:
    >>> rest_api_parameters({'courses':[{'id':1,'name': 'course1'}]})
    {'courses[0][id]':1,
     'courses[0][name]':'course1'}
    """
    if out_dict is None:
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


def call_mdl_function(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.

    Source: https://github.com/mrcinv/moodle_api.py/blob/master/moodle_api.py

    Example:
    >>> call_mdl_function('core_course_update_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update({'wstoken': CONFIG['moodle']['token'],
                       'moodlewsrestformat': 'json', 'wsfunction': fname})
    response = requests.post(urllib.parse.urljoin(CONFIG['moodle']['url'], CONFIG['moodle']['endpoint']), parameters)
    logger.debug('Response Encoding: {}, Best guess: {}'.format(response.encoding, response.apparent_encoding))
    response = response.json()
    if type(response) == dict and response.get('exception'):
        raise SystemError('Error calling Moodle API', response)
    return response


def download_image(link, directory):
    try:
        download_image.counter += 1
    except AttributeError:
        download_image.counter = 1
    logger.info('Loading image from {}'.format(link))
    if CONFIG['moodle']['url'] in link:
        # get image file from Moodle by POST request with auth token
        parameters = {'token': CONFIG['moodle']['token']}
        response = requests.post(link, parameters)
    else:
        # get external image with a simple GET request
        response = requests.get(link)
    only_file_name = 'image{}'.format(download_image.counter)
    image_file_name_on_disk = os.path.join(directory, only_file_name)
    with open(image_file_name_on_disk, 'wb') as image_on_disk:
        image_on_disk.write(response.content)
    return image_file_name_on_disk


################################## User and Course functions ##################################

def get_token_for_user(username, password, servicename='moodle_mobile_app'):
    login_url = 'login/token.php?username={username}&password={password}&service={servicename}'
    token_url = urllib.parse.urljoin(CONFIG['moodle']['url'], login_url)
    url = token_url.format(username=username, password=password, servicename=servicename)
    r = requests.get(url)
    return r.json()['token']


def get_courses_for_user(userid=None):
    if not userid:
        userid = get_user_id()
    response = call_mdl_function('core_enrol_get_users_courses', userid=userid)
    # check whether user is teacher: core_enrol_get_enrolled_users
    return [(c['id'], c['fullname']) for c in response]


def get_user_id():
    response = call_mdl_function('core_webservice_get_site_info')
    user_id = response['userid']
    return user_id


def get_content_for_course(courseid):
    """
    Gets all activities and materials for a given course. The returned list
    contains tuple with the id and name of the course section and the id, name
    and type of the element.
    """
    content = call_mdl_function('core_course_get_contents', courseid=courseid)
    result = []
    for c in content:
        for m in c['modules']:
            result.append((c['id'], c['name'], m['id'], m['name'], m['modname'], m['visible'], m['uservisible'],
                          m['visibleoncoursepage'], m['modicon']))
    return result


############################## Glossary functions ##############################

def get_glossaries_from_course(courseid):
    id_list = []
    response = call_mdl_function('mod_glossary_get_glossaries_by_courses', courseids=[courseid])
    for g in response['glossaries']:
        id_list.append((g['id'], g['name']))
    return id_list


def get_entries_for_glossary(glossary_id, directory):
    entries = call_mdl_function('mod_glossary_get_entries_by_letter', id=glossary_id, letter='ALL', limit=1000)
    with open(os.path.join(directory, 'loaded_data_{}.xml'.format(glossary_id)), 'w', encoding='utf8') as f:
        f.write(str(entries))
    no = entries['count']
    logger.info('Found {} entries in glossary.'.format(no))
    if 'attachment' in entries and entries['attachment']:
        for a in entries['attachments']:
            logger.info('Found attachment for entry: {}'.format(a))
    for e in entries['entries']:
        yield (e['concept'], e['definition'])


############################## Database functions #############################

def get_databases_by_courses(courseid):
    id_list = []
    response = call_mdl_function('mod_data_get_databases_by_courses', courseids=[courseid])
    for d in response['databases']:
        id_list.append((d['id'], d['name'], d['singletemplate'], d['listtemplate']))  # d['intro']???
    return id_list


def get_fields_for_database(databaseid):
    response = call_mdl_function('mod_data_get_fields', databaseid=databaseid)
    return [(f['type'], f['name'], f['description']) for f in response['fields']]


def get_entries_for_database(databaseid):
    entry_list = []
    # get field names and types
    fields = get_fields_for_database(databaseid)
    # get entries
    entries = call_mdl_function('mod_data_get_entries', databaseid=databaseid, returncontents='1')
    no = entries['totalcount']
    logger.info('Found {} entries in glossary.'.format(no))
    # handle all entries
    for e in entries['entries']:
        entry_data = {'id': e['id'], 'files': {}}
        for i, d in enumerate(e['contents']):
            entry_data[fields[i][1]] = d['content']
            for f in d['files']:
                entry_data['files'][f['filename']] = f['fileurl']
                logger.info('Found attached file for database entry: {} (URL: {})'.format(f['filename'], f['fileurl']))
        entry_list.append(entry_data)
    return entry_list


################################ Wiki functions #################################

def get_wikis_by_courses(courseid):
    id_list = []
    response = call_mdl_function('mod_wiki_get_wikis_by_courses', courseids=[courseid])
    for w in response['wikis']:
        id_list.append((w['id'], w['name'], w['firstpagetitle'], w['wikimode'], w['defaultformat'], w['visible']))
    return id_list


def get_subwikis(wikiid):
    id_list = []
    response = call_mdl_function('mod_wiki_get_subwikis', wikiid=wikiid)
    for s in response['subwikis']:
        id_list.append((s['id'], s['wikiid']))
    return id_list


def get_subwiki_pages(wikiid):
    # Alternatively the API call "mod_wiki_get_page_contents" could be used.
    id_list = []
    response = call_mdl_function('mod_wiki_get_subwiki_pages ', wikiid=wikiid)
    for p in response['pages']:
        id_list.append((p['id'], p['title'], p['cachedcontent']))
    return id_list

########################### Miscellaneous functions ###########################


def edit_module(action, module_id):
    """
    Performs an action on course module (change visibility, duplicate, delete,
    etc.)

    Parameter "action": hide, show, stealth, duplicate, delete, moveleft,
                        moveright, group...
    Parameter "sectionreturn" defaults to null
    """
    try:
        response = call_mdl_function('core_course_edit_module', action=action, id=module_id)
        new_html = response
        return True
    except SystemError as e:
        # SystemError: ('Error calling Moodle API',
        # {'exception': 'required_capability_exception',
        #  'errorcode': 'nopermissions',
        #  'message': 'Sie haben derzeit keine Rechte, dies zu tun
        #              (Aktivitäten anzeigen / verbergen).'})
        if 'Sie haben derzeit keine Rechte' in e.args[1]['message']:
            logger.error('No permission to edit the given module!')
        return False


def hide_module(module_id):
    return edit_module('hide', module_id)


def show_module(module_id):
    return edit_module('show', module_id)


def get_string(stringid, component, lang):
    """
    Return a translated string - similar to core get_string(), call

    Parameter stringparams (Default to "Array ( ) ")

    core_get_strings -> Return some translated strings - like several core get_string(), calls

    Solution:  Adding a new external web service solved my issue?!?!??!
    """
    id_list = []
    response = call_mdl_function('core_get_string', stringid=stringid, component=component, lang=lang)
    print(response)
    # for s in response['subwikis']:
    #     id_list.append((s['id'], s['wikiid']))
    return id_list


# TODO:
# core_user_create_users
# core_message_get_messages
# core_course_edit_section    # Performs an action on course section (change visibility, set marker, delete)
