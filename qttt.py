#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui

from main_ui import Ui_MainWindow

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.gb_current.hide()

#        self.resize(250, 150)
#        self.setWindowTitle('statusbar')

#        self.statusBar().showMessage('Ready')

app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())
