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
from data import Section
from guilib import CredentialsDialog, get_resource_path


logger = logging.getLogger('moodleeditor')


class MoodleEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super(MoodleEditor, self).__init__()
        uic.loadUi(get_resource_path('moodleeditor.ui'), self)
        
        self.tempDir = tempfile.TemporaryDirectory()
        self.iconMap = {}

        self.siteNode = self.moodleItemsTreeWidget.topLevelItem(0)
        self.siteNode.setIcon(0, QtGui.QIcon(get_resource_path('res/home.svg')))
        header = self.moodleItemsTreeWidget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.setWindowIcon(QtGui.QIcon(get_resource_path('res/moodle.png')))
        self.setupStatusBar()
        self.addSlotsAndSignals()
        self.show()

    def setupStatusBar(self):
        self.statusBar().showMessage(self.tr('MoodleEditor'))
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setMaximum(100)
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.setValue(0)

    def addSlotsAndSignals(self):
        self.userCanChoose = False
        self.moodleItemsTreeWidget.itemDoubleClicked.connect(self.handleClick)
        self.moodleItemsTreeWidget.itemChanged.connect(self.handleChange)
        self.actionInfo.triggered.connect(self.showInfoDialog)
        self.actionSet_Site.triggered.connect(self.showSiteDialog)

    def handleClick(self, item, column):
        logger.debug('Double click on item {} in column {}.'.format(item.text, column))
        if item == self.siteNode:
            logger.info('Changing site URL...')
            self.showSiteDialog()
        elif item.parent() == self.siteNode:
            logger.info('Loading activities and material for chosen course...')
            id, _ = item.data(0, QtCore.Qt.UserRole)
            self.populateActivities(item, id)

    def handleChange(self, changedItem, column):
        if self.userCanChoose and column == 1:
            dataForChangedItem = changedItem.data(0, QtCore.Qt.UserRole)
            if type(dataForChangedItem) == Section:
                self.statusBar().showMessage(self.tr('Changing visibility for section...'))
                logger.info('Changing visibility of section {}.'.format(dataForChangedItem.name))
                childCount = changedItem.childCount()
                for i in range(childCount):
                    child = changedItem.child(i)
                    moodleItem = child.data(0, QtCore.Qt.UserRole)
                    id = moodleItem[2]
                    checked = changedItem.checkState(1)
                    self.changeVisibilityForModule(id, checked)
                    if checked > 0:
                        child.setCheckState(1, QtCore.Qt.Checked)
                    else:
                        child.setCheckState(1, QtCore.Qt.Unchecked)
                    self.progressBar.setValue(100 / childCount * (i + 1))
            else:
                self.statusBar().showMessage(self.tr('Changing visibility for module...'))
                id = dataForChangedItem[2]
                checked = changedItem.checkState(1)
                self.changeVisibilityForModule(id, checked)
            self.statusBar().showMessage(self.tr('Visibility changed.'))

    ############################## Site wide ##############################

    def setSiteURL(self, url):
        CONFIG['moodle']['url'] = url
        self.siteNode.setText(0, self.tr('Moodle Site ({})').format(CONFIG['moodle']['url']))

    def getCredentials(self):
        dlg = CredentialsDialog(self)
        if dlg.exec_():
            try:
                CONFIG['moodle']['token'] = moodle.get_token_for_user(*dlg.getCredentials(), 'wichmann_tools')
                self.populateCourses()
                return True
            except requests.exceptions.MissingSchema as e:
                logger.error('Could not connect to Moodle site: {}'.format(e))
                return False
            except KeyError as e:
                logger.error('Wrong credentials entered: {}'.format(e))
                return False

    def showSiteDialog(self):
        self.statusBar().showMessage(self.tr('Logging in to Moodle site...'))
        DEFAULT_SITE_URL = 'https://moodle.nibis.de/bbs_osb/'
        text, okPressed = QtWidgets.QInputDialog.getText(self, self.tr('Enter site URL'), self.tr('Site URL:'),
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
                QtWidgets.QMessageBox.warning(self, self.tr('Error'), self.tr('Wrong site URL or credentials.'),
                                              QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            self.statusBar().showMessage(self.tr('Logged in.'))

    ############################## Course wide ##############################

    def populateCourses(self):
        # get all courses for current user
        courses = moodle.get_courses_for_user()
        # add items for all courses
        self.progressBar.setValue(0)
        for i, c in enumerate(courses):
            courseNode = QtWidgets.QTreeWidgetItem(self.siteNode)
            courseNode.setText(0, c[1])
            courseNode.setData(0, QtCore.Qt.UserRole, c)
            #courseNode.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            courseNode.setIcon(0, QtGui.QIcon(get_resource_path('res/course.svg')))
            self.progressBar.setValue(100 / len(courses) * (i + 1))
            #QtGui.qApp.processEvents()
        self.siteNode.setExpanded(True)

    def removeCourses(self):
        self.siteNode.takeChildren()

    ############################## Module wide ##############################

    def changeVisibilityForModule(self, id, checked):
        logger.info('Changed visibility of module {} to {}'.format(id, checked))
        if checked > 0:
            moodle.show_module(id)
        else:
            moodle.hide_module(id)

    def populateActivities(self, topItem, course_id):
        self.statusBar().showMessage(self.tr('Loading all modules for course...'))
        self.userCanChoose = False
        activities = moodle.get_content_for_course(course_id)
        self.progressBar.setValue(0)
        for i, a in enumerate(activities):
            activitiesNode = QtWidgets.QTreeWidgetItem(self.findSectionItem(topItem, a[0], a[1]))
            activitiesNode.setText(0, '{} ({})'.format(a[3], a[4]))
            activitiesNode.setIcon(0, QtGui.QIcon(self.getIcon(a[8])))
            activitiesNode.setData(0, QtCore.Qt.UserRole, a)
            if a[5] == 1:
                activitiesNode.setCheckState(1, QtCore.Qt.Checked)
            elif a[5] == 0:
                activitiesNode.setCheckState(1, QtCore.Qt.Unchecked)
            self.progressBar.setValue(100 / len(activities) * (i + 1))
        topItem.setExpanded(True)
        self.userCanChoose = True
        self.statusBar().showMessage(self.tr('All modules loaded.'))

    def findSectionItem(self, topItem, sectionId, sectionName):
        for i in range(topItem.childCount()):
            # check all children of course node for section
            c = topItem.child(i)
            data = c.data(0, QtCore.Qt.UserRole)
            if data.id == sectionId and data.name == sectionName:
                return c
        # create new section node, if it does not already exists
        sectionNode = QtWidgets.QTreeWidgetItem(topItem)
        sectionNode.setText(0, '{}'.format(sectionName))
        sectionNode.setIcon(0, QtGui.QIcon(get_resource_path('res/section.svg')))
        sectionData = Section(sectionId, sectionName)
        sectionNode.setData(0, QtCore.Qt.UserRole, sectionData)
        sectionNode.setCheckState(1, QtCore.Qt.Checked)
        sectionNode.setExpanded(True)
        return sectionNode

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
                return get_resource_path('res/home.svg')

    def showInfoDialog(self):
        QtWidgets.QMessageBox.information(self, self.tr('About...'), self.tr('MoodleEditor from Christian Wichmann\nSource: https://github.com/wichmann/moodle2pdf'),
                                          QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

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
    translator = QtCore.QTranslator()
    translator.load('translate/{}.qm'.format(QtCore.QLocale.system().name()))
    app.installTranslator(translator)
    window = MoodleEditor()
    sys.exit(app.exec_())
