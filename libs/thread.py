
from PyQt5.QtCore import QRunnable, QObject, QThreadPool, QThread ,pyqtSignal
from bin.im import *

class mThread(QRunnable):
    def __init__(self):
        super(mThread, self).__init__()
        self.model = None
        self.communicate = None
    def transfer(self, task=None,communicate=None):
        self.task = task
        self.communicate = communicate

    def run(self):
        if self.task:
            im = IM()
            im.run(self.task)
            #self.task["status"] = status
            #self.communicate.emit(self.task)
