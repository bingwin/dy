from PyQt5.Qt import *
from ui.mainForm import Ui_Form
from PyQt5.QtCore import QRegExp,Qt,QTime,QRect,pyqtSignal
from libs.thread import *

class FormWindow(QWidget,Ui_Form):
    communicate = pyqtSignal(dict)
    def __init__(self):
        super(FormWindow,self).__init__()
        self.setupUi(self)
        self.setWindowTitle(u"Aweme-SendMsg")
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['pid','状态', 'user_id', '关注数', '粉丝数', '已发送','消息'])
        self.tableViewPro.setModel(self.model)
        self.tableViewPro.setColumnWidth(0, 50)
        self.tableViewPro.setColumnWidth(1, 80)
        self.tableViewPro.setColumnWidth(2, 80)
        self.tableViewPro.setColumnWidth(3, 80)
        self.tableViewPro.setColumnWidth(4, 80)
        self.tableViewPro.setColumnWidth(5, 80)
        self.tableViewPro.setColumnWidth(6, 280)
        self.tableViewPro.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 固定列宽
        self.tableViewPro.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableViewPro.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableViewPro.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tableViewPro.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.tableViewPro.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tableViewPro.setSelectionBehavior(QAbstractItemView.SelectRows)  # 整行选取
        self.tableViewPro.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 不可编辑

        regExp = QRegExp('^((2[0-4]\d|25[0-5]|[1-9]?\d|1\d{2})\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?):\d{1,5}$')
        self.lineEdit.setValidator(QRegExpValidator(regExp, self))
        self.lineEdit.setFont(QFont("Timers", 28, QFont.Bold))
        self.pool = QThreadPool()
        self.pool.globalInstance()  # 获得这个全局线程池
        self.communicate
    def startPro(self):
        print("startPro")
        task_list = IM.getLocalTask(self)
        queue = Queue()
        for task in task_list:
            queue.put(task)

        self.pool.setMaxThreadCount(int(self.spinBoxProNum.value()))
        while True:
            if queue.empty():
                print("备份队列为空")
                task = None
            else:
                print("取备份任务")
                bak_info = queue.get_nowait()
                task = Task()
                task.task_info = json.loads(bak_info.get("task_info"))
                task.user_info = json.loads(bak_info.get("user_info"))
                task.uids = json.loads(bak_info.get("uids")) if bak_info.get("uids") else None
                task.status = 1

                othread = mThread()
                othread.transfer(task=task, communicate=self.communicate)

                def setStatus(items):
                    self.model.item(items["index"], 4).setText(items["status"])

                self.communicate.connect(setStatus)
                self.pool.start(othread)
            time = QTime()
            time.start()
            while time.elapsed() < 5000:
                QCoreApplication.processEvents()



    def stopPro(self):
        print("stopPro")


if __name__ == '__main__':
    import  sys
    app = QApplication(sys.argv)
    main = FormWindow()
    main.show()
    sys.exit(app.exec_())