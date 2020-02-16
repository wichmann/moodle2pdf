#!/usr/bin/env python3

"""
Moodle Editor to change data on a Moodle site via GUI interface.
"""

import os
import sys
import logging
import tempfile
import logging.handlers

import requests
from PyQt5 import QtGui, QtWidgets, Qt, uic, QtCore

import moodle
from config import CONFIG
from gui import CredentialsDialog
from moodle2pdf_cli import build_pdf_for_glossaries


logger = logging.getLogger('moodleeditor')


class MoodleEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super(MoodleEditor, self).__init__()
        uic.loadUi('moodleeditor.ui', self)
        
        self.tempDir = tempfile.TemporaryDirectory()
        self.iconMap = {}

        self.siteNode = self.moodleItemsTreeWidget.topLevelItem(0)
        self.siteNode.setIcon(0, QtGui.QIcon('res/home.svg'))
        header = self.moodleItemsTreeWidget.header()
        #header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.addSlotsAndSignals()
        self.show()

    def setSiteURL(self, url):
        CONFIG['moodle']['url'] = url
        self.siteNode.setText(0, 'Moodle Site ({})'.format(CONFIG['moodle']['url']))

    def getCredentials(self):
        dlg = CredentialsDialog(self)
        if dlg.exec_():
            try:
                CONFIG['moodle']['token'] = moodle.get_token_for_user(*dlg.getCredentials())
                self.populateCourses()
                return True
            except requests.exceptions.MissingSchema as e:
                logger.error('Could not connect to Moodle site: {}'.format(e))
                return False

    def populateCourses(self):
        # get all courses for current user
        courses = moodle.get_courses_for_user()
        # add items for all courses
        for c in courses:
            courseNode = QtWidgets.QTreeWidgetItem(self.siteNode)
            courseNode.setText(0, c[1])
            courseNode.setData(0, QtCore.Qt.UserRole, c)
            #courseNode.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.siteNode.setExpanded(True)

    def removeCourses(self):
        self.siteNode.takeChildren()

    def addSlotsAndSignals(self):
        self.userCanChoose = False
        self.moodleItemsTreeWidget.itemDoubleClicked.connect(self.handleClick)
        self.moodleItemsTreeWidget.itemChanged.connect(self.handleChange)
        self.actionInfo.triggered.connect(self.showInfoDialog)
        self.actionSet_Site.triggered.connect(self.showSiteDialog)

    def handleClick(self, item, column):
        logger.debug('Double click on item {} in column {}.'.format(item, column))
        if item == self.siteNode:
            logger.info('Changing site URL...')
            self.showSiteDialog()
        elif item.parent() == self.siteNode:
            logger.info('Loading activities and material for chosen course...')
            id, _ = item.data(0, QtCore.Qt.UserRole)
            self.populateActivities(item, id)

    def showSiteDialog(self):
        DEFAULT_SITE_URL = 'https://moodle.nibis.de/bbs_osb/'
        text, okPressed = QtWidgets.QInputDialog.getText(self, 'Enter site URL', 'Site URL:',
                                                         QtWidgets.QLineEdit.Normal, DEFAULT_SITE_URL)
        # check for valid URLs via RegEx (see https://daringfireball.net/2010/07/improved_regex_for_matching_urls and https://gist.github.com/gruber/8891611)
        # reg_ex = QtCore.QRegExp("""(?i)\b((?:https:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""")
        # input_validator = QRegExpValidator(reg_ex, self.le_input)
        # self.le_input.setValidator(input_validator)
        if okPressed and text != '':
            self.setSiteURL(text)
            if not self.getCredentials():
                self.setSiteURL('')
                self.removeCourses()
                QtWidgets.QMessageBox.warning(self, 'Error', 'Wrong site URL or credentials.', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def handleChange(self, item, column):
        if self.userCanChoose and column == 1:
            print(item, column)

    def populateActivities(self, item, course_id):
        self.userCanChoose = False
        activities = moodle.get_content_for_course(course_id)
        for a in activities:
            activitiesNode = QtWidgets.QTreeWidgetItem(item)
            activitiesNode.setText(0, '[{}] {}: {}'.format(a[1], a[4], a[3]))
            #activitiesNode.setText(1, '{}'.format(a[5]))
            activitiesNode.setIcon(0, QtGui.QIcon(self.getIcon(a[8])))
            activitiesNode.setData(0, QtCore.Qt.UserRole, a)
            if a[5] == 1:
                activitiesNode.setCheckState(1, QtCore.Qt.Checked)
            elif a[5] == 0:
                activitiesNode.setCheckState(1, QtCore.Qt.Unchecked)
        item.setExpanded(True)
        self.userCanChoose = True

    def getIcon(self, iconPath):
        if iconPath in self.iconMap:
            return self.iconMap[iconPath]
        else:
            r = requests.get(iconPath, stream=True)
            if r.status_code == 200:
                localFile = os.path.join(self.tempDir.name, str(hash(iconPath)))
                with open(localFile, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
                self.iconMap[iconPath] = localFile
                return localFile
            else:
                return 'res/home.svg'

    def showInfoDialog(self):
        QtWidgets.QMessageBox.information(self, 'About...', 'MoodleEditor from Christian Wichmann', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

def create_logger():
    global logger
    logger.setLevel(logging.DEBUG)
    log_to_file = logging.handlers.RotatingFileHandler(CONFIG['system']['log_filename'], maxBytes=262144, backupCount=5)
    log_to_file.setLevel(logging.DEBUG)
    logger.addHandler(log_to_file)
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.DEBUG)
    logger.addHandler(log_to_screen)


if __name__ == '__main__':
    create_logger()
    app = QtWidgets.QApplication(sys.argv)
    window = MoodleEditor()
    sys.exit(app.exec_())
