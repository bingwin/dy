# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainForm.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(630, 543)
        self.tableViewPro = QtWidgets.QTableView(Form)
        self.tableViewPro.setGeometry(QtCore.QRect(10, 50, 611, 481))
        self.tableViewPro.setObjectName("tableViewPro")
        self.horizontalLayoutWidget = QtWidgets.QWidget(Form)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 611, 41))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.spinBoxProNum = QtWidgets.QSpinBox(self.horizontalLayoutWidget)
        self.spinBoxProNum.setProperty("value", 1)
        self.spinBoxProNum.setObjectName("spinBoxProNum")
        self.horizontalLayout.addWidget(self.spinBoxProNum)
        self.pushButtonStart = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.horizontalLayout.addWidget(self.pushButtonStart)
        self.pushButtonStop = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButtonStop.setObjectName("pushButtonStop")
        self.horizontalLayout.addWidget(self.pushButtonStop)

        self.retranslateUi(Form)
        self.pushButtonStart.clicked.connect(Form.startPro)
        self.pushButtonStop.clicked.connect(Form.stopPro)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "AwemeMsg"))
        self.pushButtonStart.setText(_translate("Form", "开始"))
        self.pushButtonStop.setText(_translate("Form", "结束"))


