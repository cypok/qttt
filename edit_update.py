from PyQt4 import QtGui, QtCore
from edit_update_ui import Ui_Dialog
from time import mktime

def datetime2QDateTime(dt):
    return QtCore.QDateTime.fromTime_t(int(mktime(dt.timetuple())))

class EditUpdate(QtGui.QDialog, Ui_Dialog):
    def __init__(self, update, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)

        self.update = update
        self.message.setText(update.message)
        self.started_at.setDateTime(datetime2QDateTime(update.started_at))

        if update.finished_at is not None:
            self.finished_at.setDateTime(datetime2QDateTime(update.finished_at))
        else:
            self.grid.removeWidget(self.finished_at)
            self.grid.removeWidget(self.label_finished_at)
            self.finished_at.close()
            self.label_finished_at.close()

        if update.hours is not None:
            self.hours.setValue(update.hours)
        else:
            self.grid.removeWidget(self.hours)
            self.grid.removeWidget(self.label_hours)
            self.hours.close()
            self.label_hours.close()

        self.grid.invalidate()

    def changed_update(self):
        pass
