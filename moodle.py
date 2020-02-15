
import logging
import urllib.parse

import requests

from config import CONFIG


logger = logging.getLogger('moodle2pdf.moodle')


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


def call_mdl_function(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.

    Source: https://github.com/mrcinv/moodle_api.py/blob/master/moodle_api.py

    Example:
    >>> call_mdl_function('core_course_update_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update(
        {"wstoken": CONFIG['moodle']['key'], 'moodlewsrestformat': 'json', "wsfunction": fname})
    response = requests.post(urllib.parse.urljoin(CONFIG['moodle']['url'], CONFIG['moodle']['endpoint']), parameters)
    #response.encoding = 'utf-8' # r.apparent_encoding
    #print(response.encoding, response.apparent_encoding)
    response = response.json()
    if type(response) == dict and response.get('exception'):
        raise SystemError("Error calling Moodle API\n", response)
    return response


def get_courses_for_user():
    response = call_mdl_function('core_enrol_get_users_courses', userid=get_user_id())
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
            result.append( (c['id'], c['name'], m['id'], m['name'], m['modname']) )
    return result


def get_glossaries_from_course(courseid):
    id_list = []
    response = call_mdl_function('mod_glossary_get_glossaries_by_courses',
                    courseids=[courseid])
    for g in response['glossaries']:
        id_list.append((g['id'], g['name']))
    return id_list


def get_entries_for_glossary(glossary_id):
    entries = call_mdl_function('mod_glossary_get_entries_by_letter',
                   id=glossary_id, letter='ALL', limit=1000)
    with open('loaded_data_{}.xml'.format(glossary_id), 'w') as f:
        f.write(str(entries))
    no = entries['count']
    logger.info('Found {} entries in glossary.'.format(no))
    if 'attachment' in entries and entries['attachment']:
        for a in entries['attachments']:
            logger.info('Found attachment for entry: {}'.format(a))
    for e in entries['entries']:
        yield (e['concept'], e['definition'])


def download_image(link):
    try:
        download_image.counter += 1
    except AttributeError:
        download_image.counter = 1
    # , 'moodlewsrestformat': 'json'} #, "wsfunction": fname}
    parameters = {"token": CONFIG['moodle']['key']}
    logger.info('Loading image from {}'.format(link))
    response = requests.post(link, parameters)
    image_file_name_on_disk = 'image{}.png'.format(download_image.counter)
    with open(image_file_name_on_disk, 'wb') as image_on_disk:
        image_on_disk.write(response.content)
    return image_file_name_on_disk
