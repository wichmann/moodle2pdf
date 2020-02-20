#!/usr/bin/env python3

"""
Moodle2PDF loads data directly from Moodle glossaries and creates a PDF file
with the formatted entries as a GUI version.
"""

import sys
import logging
import webbrowser
import logging.handlers

import requests
from PyQt5 import QtGui, QtWidgets, Qt, uic, QtCore

import moodle
from config import CONFIG
from gui import CredentialsDialog
from moodle2pdf_cli import build_pdf_for_glossaries


logger = logging.getLogger('moodle2pdf')


class Moodle2PdfWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(Moodle2PdfWindow, self).__init__()
        uic.loadUi('moodle2pdf.ui', self)
        
        self.siteNode = self.moodleItemsTreeWidget.topLevelItem(0)
        self.siteNode.setIcon(0, QtGui.QIcon('res/home.svg'))
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
            courseNode.setIcon(0, QtGui.QIcon('res/course.svg'))
        self.siteNode.setExpanded(True)

    def removeCourses(self):
        self.siteNode.takeChildren()

    def addSlotsAndSignals(self):
        self.moodleItemsTreeWidget.itemDoubleClicked.connect(self.handleClick)
        self.exportButton.clicked.connect(self.exportGlossaries)
        self.actionInfo.triggered.connect(self.showInfoDialog)
        self.actionSet_Site.triggered.connect(self.showSiteDialog)

    def handleClick(self, item, column_no):
        logger.debug('Double click on item {} in column {}.'.format(item, column_no))
        if item == self.siteNode:
            logger.info('Changing site URL...')
            self.showSiteDialog()
        elif item.parent() == self.siteNode:
            logger.info('Loading glossaries for chosen course...')
            id, _ = item.data(0, QtCore.Qt.UserRole)
            self.populateGlossaries(item, id)

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

    def populateGlossaries(self, item, course_id):
        glossaries = moodle.get_glossaries_from_course(course_id)
        for g in glossaries:
            glossaryNode = QtWidgets.QTreeWidgetItem(item)
            glossaryNode.setText(0, g[1])
            glossaryNode.setData(0, QtCore.Qt.UserRole, g)
            glossaryNode.setCheckState(0, QtCore.Qt.Unchecked)
            glossaryNode.setIcon(0, QtGui.QIcon('res/glossar.svg'))
        item.setExpanded(True)

    def exportGlossaries(self):
        selectedGlossaries = []
        for item in self.moodleItemsTreeWidget.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive, 0):
            if item.checkState(0) > 0:
                glossaryItem = item.data(0, QtCore.Qt.UserRole)
                logger.debug('Item selected: {}'.format(glossaryItem[1]))
                selectedGlossaries.append(glossaryItem)
        if selectedGlossaries:
            if self.combineGlossariesCheckBox.checkState() > 0:
                default_output_file = CONFIG['pdf']['default_output_filename']
                options = QtWidgets.QFileDialog.Options()
                #options |= QtWidgets.QFileDialog.DontUseNativeDialog
                output_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as PDF File...', default_output_file,
                                                                    'PDF File (*.pdf)', options=options)
                if output_file:
                    build_pdf_for_glossaries(selectedGlossaries, output_file)
                    # open file with associated application (there is no really good
                    # solution, see https://stackoverflow.com/a/17317468 and
                    # https://stackoverflow.com/a/21987839)
                    webbrowser.open(output_file)
            else:
                logger.error('Not implemented yet!')
                QtWidgets.QMessageBox.warning(self, 'Error', 'This function is not implemented yet.', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'You have to select some glossaries first.', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def showInfoDialog(self):
        QtWidgets.QMessageBox.information(self, 'About...', 'Moodle2PDF from Christian Wichmann\nSource: https://github.com/wichmann/moodle2pdf', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

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
    window = Moodle2PdfWindow()
    sys.exit(app.exec_())