
import os
import sys
import logging

from PyQt5 import QtWidgets


logger = logging.getLogger('moodle2pdf.gui')


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    Source: https://stackoverflow.com/a/13790741
    """
    logger.debug('Looking for resource: {}'.format(relative_path))
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    logger.debug('Resource should be at: {}'.format(base_path))
    return os.path.join(base_path, relative_path)


class CredentialsDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(CredentialsDialog, self).__init__(*args, **kwargs)
        
        self.setWindowTitle('Enter credentials...')
        
        usernameLabel = QtWidgets.QLabel('Username: ')
        self.usernameLineEdit = QtWidgets.QLineEdit()
        self.usernameLineEdit.setPlaceholderText('username')
        usernameHBox = QtWidgets.QHBoxLayout()
        usernameHBox.addWidget(usernameLabel)
        usernameHBox.addWidget(self.usernameLineEdit)

        passwordLabel = QtWidgets.QLabel('Password: ')
        self.passwordLineEdit = QtWidgets.QLineEdit()
        self.passwordLineEdit.setPlaceholderText('password')
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        passwordHBox = QtWidgets.QHBoxLayout()
        passwordHBox.addWidget(passwordLabel)
        passwordHBox.addWidget(self.passwordLineEdit)

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(usernameHBox)
        self.layout.addLayout(passwordHBox)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def getCredentials(self):
        return self.usernameLineEdit.text(), self.passwordLineEdit.text()
