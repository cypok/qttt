#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui

from main_ui import Ui_MainWindow
import yaml
import os

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def load_settings(self):
        with open(os.environ['HOME']+'/.tttrc') as f:
            self.settings = yaml.load(f.read())

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.gb_current.hide()

        self.move(400, 100)
        self.resize(350, 550)

        self.load_settings()

        self.setWindowTitle("QTTT - %s" % self.settings['base_url'])


app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())
