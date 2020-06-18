import csv
import codecs
import time
import os
import numpy as np          #importing the python libraries
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QFileInfo
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTextStream
from PyQt5.QtCore import QProcess
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QAbstractItemView
import matplotlib.pyplot as plt;
#importing the pyqt5 and matplotlib libraries on project
plt.rcdefaults()


class Homepage(QMainWindow):
    def __init__(self):
        super(Homepage, self).__init__()

        self.path = QDir('C:/Speedtest_Save')
        if not QDir.exists(self.path):
            print("Folder is not Exisiting! Please Wait till it create New.......")     #if the folder doesn't exist it throws error message
            dir = QDir()
            newfolder = 'C:/SpeedTest_Save' #Creating the new folder
            dir.mkpath(newfolder)
        self.myfile = 'C:/SpeedTest_Save' + '/Speedtest_results.csv' #saving the file
        self.isChanged = False
        self.setStyleSheet(design(self))
        self.speedtestExec = "C:/Users/jagan/speedtest-cli.exe"     #executable file path for the speedtest

        self.cmd = ''
        print("Cmd started")
        self.list = []
        print("list started")
        self.date = ""
        print("date started")
        self.time = ""
        print("time started")
        self.download = ""
        print("download started")
        self.upload = ""
        print("upload started")
        self.ping = ""
        print("Ping started")
        self.server = ""
        print("Server started")
        self.process = QProcess(self)
        print("Process Started")

        self.process.started.connect(lambda: self.showMessage("Speed Test Has Been Started"))       #showing the test messages
        print("Test Started")

        print("Test Completed")
        self.process.finished.connect(self.processFinished)
        self.process.readyRead.connect(self.processOut)

        self.tableview = QTableWidget()
        print("Table creation success")
        self.tableview.setColumnCount(6)
        print("Process Started")
        self.setHeaders()
        print("Process Started for the headers")
        self.tableview.verticalHeader().setVisible(False)
        print("Process Started")
        self.tableview.horizontalHeader().setVisible(False)
        print("Process Started")
        self.tableview.setSelectionBehavior(QAbstractItemView.SelectRows)
        print("Process Started")
        self.setCentralWidget(self.tableview)
        self.setWindowIcon(QIcon.fromTheme('network'))
        self.toolbarcreation()
        self.createStatusBar()

        self.readSettings()
        print("read setting started")

        self.combofillbox()
        self.title = "frame"
        self.setMinimumSize(440, 220)

    def displaychartdownload(self):         #Ploting the download graph
        data = []
        for row in range(self.tableview.rowCount()):
            data.append(float(self.tableview.item(row, 2).text()))
        print(data)
        performance = data
        y_pos = np.arange(len(performance))
        plt.bar(y_pos, performance, align='center', alpha=0.5)
        plt.xticks(y_pos, "")
        plt.ylabel('Mbit/s')
        plt.title('Speed Test Chart - Download')
        plt.show()

    def displaychartupload(self):           #plotting the upload chart
        plt.rcParams['toolbar'] = 'None'
        data = []
        for row in range(self.tableview.rowCount()):
            data.append(float(self.tableview.item(row, 3).text()))
        print(data)
        performance = data
        y_pos = np.arange(len(performance))
        plt.bar(y_pos, performance, align='center', alpha=0.5)
        plt.xticks(y_pos, "")
        plt.ylabel('Mbit/s')
        plt.title('Speed Test Chart - Upload')
        plt.tight_layout()
        plt.show()

    def combofillbox(self):         #creating a toolbar function
        plt.rcParams['toolbar'] = 'None'
        cmd = self.speedtestExec + " --list"        #speedtest executable file
        serverlist = []
        myprocess = QProcess()
        myprocess.start(cmd)
        myprocess.waitForFinished(-1)
        output = str(myprocess.readAll(), encoding='utf8').rstrip()
        serverlist.append(output)
        out = ','.join(serverlist)
        out = out.partition("Retrieving speedtest.net configuration...")[2]     #Retreieving the speedtest configurations
        out = out.partition('\n')[2]
        mylist = out.rsplit('\n')
        self.combo.addItem("auto")
        self.combo.addItems(mylist)
        self.combo.setCurrentIndex(1)

    def setHeaders(self):           #setting width of the column
        self.tableview.horizontalHeader().setVisible(False)
        font = QFont()
        font.setPointSize(8)
        self.tableview.horizontalHeader().setFont(font)     #setting the table view
        self.tableview.setColumnWidth(0, 80)
        self.tableview.setColumnWidth(1, 60)
        self.tableview.setColumnWidth(2, 70)
        self.tableview.setColumnWidth(3, 60)
        self.tableview.setColumnWidth(4, 60)
        self.tableview.setColumnWidth(5, 100)
        self.tableview.setHorizontalHeaderItem(0, QTableWidgetItem("Date"))
        self.tableview.setHorizontalHeaderItem(1, QTableWidgetItem("Time"))
        self.tableview.setHorizontalHeaderItem(2, QTableWidgetItem("Download"))
        self.tableview.setHorizontalHeaderItem(3, QTableWidgetItem("Upload"))
        self.tableview.setHorizontalHeaderItem(4, QTableWidgetItem("Ping"))
        self.tableview.setHorizontalHeaderItem(5, QTableWidgetItem("Server"))

    def showMessage(self, message):     #displaying the status bar message
        self.statusBar().showMessage(message)

    def closeEvent(self, event):    #saving the Output file on CSV
        self.writeSettings()
        if self.isChanged == True:
            self.createCSV()
        event.accept()

    def createActions(self):
        root = QFileInfo(__file__).absolutePath()

    def toolbarcreation(self):      #creating the frames
        self.tb = self.addToolBar("File")
        self.title = "PyQt5 Frame"
        self.tb.setMovable(False)
        self.testAct = QAction(QIcon.fromTheme('media-playback-start'), "Start", self,
                               statusTip="Speed Test Has Been Started",
                               triggered=self.startTest)
        self.tb.addAction(self.testAct)
        self.combo = QComboBox()
        self.combo.setFixedWidth(400)
        self.tb.addWidget(self.combo)
        self.chartActD = QAction(QIcon.fromTheme('chart'), "Graph For Download Speed", self,
                                 statusTip="show Chart",
                                 triggered=self.displaychartdownload)
        self.tb.addAction(self.chartActD)
        self.chartActU = QAction(QIcon.fromTheme('chart'), "Graph for Upload Speed", self,
                                 statusTip="show Chart",
                                 triggered=self.displaychartupload)
        self.tb.addAction(self.chartActU)

    def startTest(self):        #Starting the speedtest
        self.started = time.time()
        self.list = []
        self.date = ""
        self.time = ""
        self.download = ""
        self.upload = ""
        self.ping = ""
        self.server = ""
        if self.combo.currentText() == "automatic_server":
            print("automatic_server Started")
            self.cmd = self.speedtestExec
        else:
            myserver = self.combo.currentText().partition(")")[0]
            self.cmd = self.speedtestExec + " --server " + myserver
        print("Speed Test started *** " + self.cmd)
        if QFile.exists(self.speedtestExec):
            self.process.start(self.cmd)
        else:
            self.showMessage("Connection to the server is not reachable")

    def createStatusBar(self):
        self.showMessage("Ready")       #Alert Message

    def readSettings(self): #read settings
        settings = QSettings("cambria", "SpeedTest")    #Font selection
        pos = settings.value("pos", QPoint(200, 200))
        size = settings.value("size", QSize(400, 400))
        self.resize(size)
        self.move(pos)

    def writeSettings(self):        #write settings
        settings = QSettings("cambria", "SpeedTest")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())

    def addRow(self):       #adding the row and setting its date and time
        row = self.tableview.rowCount()
        newItem = QTableWidgetItem(time.strftime('%d.%m.%Y'))
        self.tableview.insertRow(row)
        self.tableview.horizontalHeader().setStretchLastSection(True)
        column = 0
        self.tableview.setItem(row, column, newItem)
        newItem = QTableWidgetItem(time.strftime('%H:%M'))
        column = 1
        self.tableview.setItem(row, column, newItem)
        newItem = QTableWidgetItem(self.download)
        column = 2
        self.tableview.setItem(row, column, newItem)
        newItem = QTableWidgetItem(self.upload)
        column = 3
        self.tableview.setItem(row, column, newItem)
        newItem = QTableWidgetItem(self.ping)
        column = 4
        self.tableview.setItem(row, column, newItem)
        newItem = QTableWidgetItem(self.server)
        column = 5
        self.tableview.setItem(row, column, newItem)
        self.isChanged = True
        last = self.tableview.rowCount() - 1
        self.tableview.selectRow(last)
        self.ended = time.time() - self.started
        m, s = divmod(time.time() - self.started, 60)
        h, m = divmod(m, 60)
        time_str = "%02d:%02d" % (m, s)
        print('Operation completed in', time_str)
        self.tableview.resizeRowsToContents()
        self.showMessage('Speed Test completed in ' + time_str)

    def processOut(self):
        try:
            output = str(self.process.readAll(), encoding='utf8').rstrip()
        except Error:
            output = str(self.process.readAll()).rstrip()
        self.list.append(output)

    def processFinished(self):
        out = ','.join(self.list)
        self.download = out.partition("Download: ")[2]
        self.download = self.download.partition(' Mbit/s')[0]

        self.upload = out.partition("Upload: ")[2]
        self.upload = self.upload.partition(' Mbit/s')[0]

        self.ping = out.partition("km]: ")[2]
        self.ping = self.ping.partition(' ms')[0]
        self.ping = self.ping.partition('.')[0]

        self.server = out.partition("Hosted by ")[2]
        self.server = self.server.partition(' [')[0]

        self.addRow()

    def createCSV(self):            #Saving and writting the data in CSV
        with open(self.myfile, 'w') as stream:
            print("saving", self.myfile)
            writer = csv.writer(stream, delimiter='\t')
            for row in range(self.tableview.rowCount()):
                rowdata = []
                for column in range(self.tableview.columnCount()):
                    item = self.tableview.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)
        self.isChanged = False


def design(self):  #Designing the font and background
    self.title = "PyQt5 Frame"
    return """
        QTableWidget
        {
            border: 1px solid grey;
            border-radius: 0px;
            font-family: arial;
            font-size: 10pt;
            background-color: #ebebeb;
            selection-color: violet
        }

            
        QTableWidget::item:selected 
        {
            color: #F4F4F4;
            background: qlineargradient(x1:0, y1:0, x1:2, y1:2, stop:0 #bfc3fb, stop:1 #324864);
        } 
    """


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    mainWin = Homepage()
    mainWin.show()
    sys.exit(app.exec_())
