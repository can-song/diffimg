"""
    Doc: 
    Created on 2022/09/07 19:37:57
    @Creator: songcan
    Last Edit on 2022/09/07
    @Last Editor: songcan
"""

import os
import sys
import os.path as osp
from PIL import Image
import numpy as np
import rasterio as rio
import geopandas as gpd
import yaml
import datetime
from PySide6.QtWidgets import QApplication, QGraphicsPolygonItem, QMessageBox, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QSpinBox, \
    QWidget, QSizePolicy, QGridLayout, QTextEdit, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, \
    QComboBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, Signal, Slot, QRectF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPolygonF, QPainter
from pathlib import Path
from PySide6.QtGui import QIcon, QKeySequence

from .context import FileList, MainUI, MouseTrack, ReferenceFileBlock, ToolBar

class LoadFileListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Load File List")
        self.setWindowIcon(QIcon('NoteBook.png'))
        self.resize(412, 412)
        self.text_edit = QTextEdit(self)
        # self.text_edit.setText("Hello World")
        self.text_edit.setPlaceholderText("Please edit text here")
        # self.text_edit.textChanged.connect(lambda: print("text is changed!"))
        
        self.save_button = QPushButton("Save", self)
        self.clear_button = QPushButton("Clear", self)
        
        self.save_button.clicked.connect(lambda: self.button_slot(self.save_button))
        self.clear_button.clicked.connect(lambda: self.button_slot(self.clear_button))
        
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        
        self.h_layout.addWidget(self.save_button)
        self.h_layout.addWidget(self.clear_button)
        self.v_layout.addWidget(self.text_edit)
        self.v_layout.addLayout(self.h_layout)
        
        self.setLayout(self.v_layout)

    def button_slot(self, button):
        if button == self.save_button:
            fileList = FileList()
            fileList.fileList = []
            for file in self.text_edit.toPlainText().strip().split('\n'):
                for suf in ['.jpg', '.JPG', '.tif', '.TIF', '.tiff', '.TIFF',
                            '.png', '.txt', '.json', '.geojson', '.shp']:
                    file = file.rstrip(suf)
                fileList.fileList.append(file)
            self.close()
            # choice = QMessageBox.question(self, "Question", "Do you want to save it?", QMessageBox.Yes | QMessageBox.No)
            # if choice == QMessageBox.Yes:
            #     # with open('First text.txt', 'w') as f:
            #     #     f.write(self.text_edit.toPlainText())
                
            # elif choice == QMessageBox.No:
            #     self.close()
        elif button == self.clear_button:
            self.text_edit.clear()
            

class LoadFilenamesWindow(QWidget):
    def __init__(self, mainWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mainWindow = mainWindow
        self.setWindowTitle("Load Filenames")
        self.setWindowIcon(QIcon('NoteBook.png'))
        self.resize(800, 400)
        self.text_edit = QTextEdit(self)
        # self.text_edit.setText("Hello World")
        # self.text_edit.setPlaceholderText("Please edit text here")
        
        filenames = []
        for view in self.mainWindow.gridView.views():
            filename = view.scene().fileDialog.fileGroupBox.fileBlocks(
                )[0].fileLineEdit.text()
            filenames.append(filename)
            # if filename:
            #     filenames.append(filename)
        self.text_edit.setText('\n'.join(filenames))
        
        # self.text_edit.textChanged.connect(lambda: print("text is changed!"))
        
        self.open_button = QPushButton("Open", self)
        self.clear_button = QPushButton("Clear", self)
        self.close_button = QPushButton("OK", self)
        
        self.open_button.clicked.connect(lambda: self.button_slot(self.open_button))
        self.clear_button.clicked.connect(lambda: self.button_slot(self.clear_button))
        self.close_button.clicked.connect(lambda: self.button_slot(self.close_button))
        
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        
        self.h_layout.addWidget(self.clear_button)
        self.h_layout.addWidget(self.open_button)
        self.h_layout.addWidget(self.close_button)
        self.v_layout.addWidget(self.text_edit)
        self.v_layout.addLayout(self.h_layout)
        
        self.setLayout(self.v_layout)

    def button_slot(self, button):
        if button == self.open_button:
            default = osp.join(os.path.expanduser('~'), 'diffimg')
            filename, filetype = QFileDialog.getOpenFileName(
                self, 'Load Filenames', default, 'txt(*.txt)')
            if osp.isfile(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read().strip())
        elif button == self.clear_button:
            self.text_edit.clear()
        elif button == self.close_button:
            filenames = self.text_edit.toPlainText().strip().split('\n')
            views = self.mainWindow.gridView.views()
            for filename, view in zip(filenames, views):
                view.scene().fileDialog.fileGroupBox.fileBlocks(
                    )[0].fileLineEdit.setText(filename)
            self.close()
            

class ExportFilenamesWindow(QWidget):
    def __init__(self, mainWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mainWindow = mainWindow
        self.setWindowTitle("Export Filenames")
        self.setWindowIcon(QIcon('NoteBook.png'))
        self.resize(800, 400)
        self.text_edit = QTextEdit(self)
        # self.text_edit.setText("Hello World")
        # self.text_edit.setPlaceholderText("Please edit text here")
        filenames = []
        for view in self.mainWindow.gridView.views():
            filename = view.scene().fileDialog.fileGroupBox.fileBlocks(
                )[0].fileLineEdit.text()
            filenames.append(filename)
            # if filename:
            #     filenames.append(filename)
        self.text_edit.setText('\n'.join(filenames))
        # self.text_edit.textChanged.connect(lambda: print("text is changed!"))
        
        self.save_button = QPushButton("Save", self)
        self.clear_button = QPushButton("Exit", self)
        
        self.save_button.clicked.connect(lambda: self.button_slot(self.save_button))
        self.clear_button.clicked.connect(lambda: self.button_slot(self.clear_button))
        
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        
        self.h_layout.addWidget(self.save_button)
        self.h_layout.addWidget(self.clear_button)
        self.v_layout.addWidget(self.text_edit)
        self.v_layout.addLayout(self.h_layout)
        
        self.setLayout(self.v_layout)

    def button_slot(self, button):
        if button == self.save_button:
            default = datetime.datetime.now().__format__('%Y-%m-%d__%H-%M-%S')+'.txt'
            default = osp.join(os.path.expanduser('~'), 'diffimg', default)
            os.makedirs(osp.dirname(default), exist_ok=True)
            filename, filetype = QFileDialog.getSaveFileName(self, 'Select File Path', default, 'txt(*.txt)')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText().strip())
            self.close()
            # choice = QMessageBox.question(self, "Question", "Do you want to save it?", QMessageBox.Yes | QMessageBox.No)
            # if choice == QMessageBox.Yes:
            # elif choice == QMessageBox.No:
            #     self.close()
        elif button == self.clear_button:
            # self.text_edit.clear()
            self.close()
            

class CloneTableWindow(QWidget):
    def __init__(self, fileBlock, *args, **kwargs):
        # super().__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle("Select Image")
        # self.setWindowIcon(QIcon('NoteBook.png'))
        # self.resize(800, 400)
        
        self.hLayout = QHBoxLayout()
        self.vLayout = QVBoxLayout()
        
        self.fileBlock = fileBlock
        gridView = MainUI().gridView
        rows, columns = gridView.rowCount(), gridView.columnCount()
        # self.resize(80*columns, 60*(rows+1))
        width, height = 60 * columns, 40 * rows
        self.resize(width+30, height + 60)
        self.tableWidget = QTableWidget(rows, columns)
        self.tableWidget.resize(width, height)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(60)
        self.tableWidget.verticalHeader().setDefaultSectionSize(40)
        self.tableWidget.horizontalHeader().hide()
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setAutoFillBackground(True)
        # self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.clicked.connect(self.clickItem)
        for column in range(columns):
            for row in range(rows):
                # item = QTableWidgetItem(f"{(row, column)}")
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                if (column + row) % 2 == 0:
                    # item.setForeground(Qt.gray)
                    item.setBackground(QColor("#CCCCCC"))
                    item.setIcon(QIcon('res/original.png'))
                    item.setText(f"{(row+1, column+1)}")
                else:
                    item.setBackground(QColor("#DDDDDD"))
                    item.setIcon(QIcon('res/modified.png'))
                    item.setText(f"{(row+1, column+1)}")
                self.tableWidget.setItem(row, column, item)
                
        self.vLayout.addWidget(self.tableWidget)
        self.setLayout(self.vLayout)
        
        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(lambda: self.clickClose())
        self.hLayout.addWidget(self.closeButton)
        self.vLayout.addLayout(self.hLayout)
    
    @Slot()
    def clickClose(self):
        self.close()
        # self.fileBlock.show()
    
    @Slot()
    def clickItem(self):
        item = self.tableWidget.selectedItems()[0]
        view = MainUI().gridView.itemAt(item.row(), item.column())
        filename = view.scene().fileDialog.fileGroupBox.fileBlocks(
                )[0].fileLineEdit.text()
        self.fileBlock.fileLineEdit.setText(filename)
        self.close()


class AdvancedSearchWindow(QWidget):
    def __init__(self, fileBlock, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("AdvanceSearch")
        # self.setWindowIcon(QIcon('NoteBook.png'))
        self.resize(800, 400)
        self.text_edit = QTextEdit(self)
        self.fileBlock = fileBlock
        cfg = self.fileBlock.advancedConfig.copy()
        cfg['mode'] = 'advance'
        self.text_edit.setText(
            yaml.dump(cfg, sort_keys=False))
        # self.text_edit.setText("Hello World")
        # self.text_edit.setPlaceholderText("Please edit text here")
        
        # filenames = []
        # for view in self.mainWindow.gridView.views():
        #     filename = view.scene().fileDialog.fileGroupBox.fileBlocks(
        #         )[0].fileLineEdit.text()
        #     filenames.append(filename)
        #     # if filename:
        #     #     filenames.append(filename)
        # self.text_edit.setText('\n'.join(filenames))
        
        # self.text_edit.textChanged.connect(lambda: print("text is changed!"))
        
        # self.open_button = QPushButton("Open", self)
        self.clear_button = QPushButton("Clear", self)
        self.close_button = QPushButton("OK", self)
        
        # self.open_button.clicked.connect(lambda: self.button_slot(self.open_button))
        self.clear_button.clicked.connect(lambda: self.button_slot(self.clear_button))
        self.close_button.clicked.connect(lambda: self.button_slot(self.close_button))
        
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        
        self.h_layout.addWidget(self.clear_button)
        # self.h_layout.addWidget(self.open_button)
        self.h_layout.addWidget(self.close_button)
        self.v_layout.addWidget(self.text_edit)
        self.v_layout.addLayout(self.h_layout)
        
        self.setLayout(self.v_layout)

    def button_slot(self, button):
        # if button == self.open_button:
        #     default = osp.join(os.path.expanduser('~'), 'diffimg')
        #     filename, filetype = QFileDialog.getOpenFileName(
        #         self, 'Load Filenames', default, 'txt(*.txt)')
        #     if osp.isfile(filename):
        #         with open(filename, 'r') as f:
        #             self.text_edit.setText(f.read().strip())
        if button == self.clear_button:
            self.text_edit.clear()
        elif button == self.close_button:
            text = self.text_edit.toPlainText()
            if text:
                cfg = yaml.load(text, yaml.FullLoader)
                self.fileBlock.advancedConfig = cfg
                mode = cfg.get('mode', 'normal')
                if mode not in {'normal', 'advance'}:
                    mode = 'normal'
                FileList().listMode = mode
                if self.fileBlock ==  ReferenceFileBlock().fileBlock:
                    self.fileBlock.updateFileList()
                self.fileBlock.updateFilename()
            else:
                FileList().listMode = 'normal'
            # filenames = self.text_edit.toPlainText().strip().split('\n')
            # views = self.mainWindow.gridView.views()
            # for filename, view in zip(filenames, views):
            #     view.scene().fileDialog.fileGroupBox.fileBlocks(
            #         )[0].fileLineEdit.setText(filename)
            self.close()
            


class LoadDataWindow(QWidget):
    def __init__(self, fileBlock, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Load Data")
        # self.setWindowIcon(QIcon('NoteBook.png'))
        self.resize(800, 400)
        self.textEdit = QTextEdit(self)
        
        fn = fileBlock.fileLineEdit.text()
        if fileBlock.loadDataCode:
            code = fileBlock.loadDataCode
        elif fileBlock.is_raster(fn):
            code = """
import rasterio as rio
class_names = None
palette = None
def load(fn, shape, crs, transform, **kwargs):
    with rio.open(fn) as ds:
        data = ds.read()
    data = data.transpose(1, 2, 0)
    data = data.squeeze()
    return data
"""
        elif fileBlock.is_vector(fn):
            code = """
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
class_names = ['background', 'road']
palette = [[0, 0, 0, 0], [255, 0, 0, 255]]
def load(fn, shape, crs, transform, **kwargs):
    gdf = gpd.read_file(fn)
    gdf = gdf[gdf.class_name=="道路"]
    gdf = gdf.to_crs(crs)
    gdf = gdf.affine_transform((~transform).to_shapely())
    geometry = gdf.geometry.apply(lambda polygon:polygon.boundary)
    shapes = geometry.values
    return rasterize(shapes, shape, fill=0, default_value=1, dtype=np.uint8)
"""
        else:
            code = ''
        self.textEdit.setText(code.strip())
        self.fileBlock = fileBlock
        
        # self.text_edit.textChanged.connect(lambda: print("text is changed!"))
        
        self.itemCombobox = QComboBox()
        if fileBlock.is_raster(fn):
            item_dir = Path(MainUI().VIEW_DIR) / 'load' / 'raster'
            for item in item_dir.rglob('*.py'):
                self.itemCombobox.addItem(item.stem)
        elif fileBlock.is_vector(fn):
            item_dir = Path(MainUI().VIEW_DIR) / 'load' / 'vector'
            for item in item_dir.rglob('*.py'):
                self.itemCombobox.addItem(item.stem)
        self.itemCombobox.textActivated.connect(self.selectItem)
        
        self.openButton = QPushButton("Open", self)
        self.saveButton = QPushButton("Save", self)
        self.closeButton = QPushButton("OK", self)
        
        self.openButton.clicked.connect(lambda: self.buttonSlot(self.openButton))
        self.saveButton.clicked.connect(lambda: self.buttonSlot(self.saveButton))
        self.closeButton.clicked.connect(lambda: self.buttonSlot(self.closeButton))
        
        self.hLayout = QHBoxLayout()
        self.vLayout = QVBoxLayout()
        
        self.hLayout.addWidget(self.itemCombobox)
        self.hLayout.addWidget(self.openButton)
        self.hLayout.addWidget(self.saveButton)
        self.hLayout.addWidget(self.closeButton)
        self.vLayout.addWidget(self.textEdit)
        self.vLayout.addLayout(self.hLayout)
        
        self.setLayout(self.vLayout)

    def selectItem(self):
        if self.fileBlock.is_raster(self.fileBlock.fileLineEdit.text()):
            fn = Path(MainUI().VIEW_DIR) / 'load' / 'raster' / (self.itemCombobox.currentText()+'.py')
        elif self.fileBlock.is_vector(self.fileBlock.fileLineEdit.text()):
            fn = Path(MainUI().VIEW_DIR) / 'load' / 'vector' / (self.itemCombobox.currentText()+'.py')
        else:
            return
        if osp.isfile(fn):
            with open(fn, 'r', encoding='utf-8') as f:
                self.textEdit.setText(f.read().strip())

    def buttonSlot(self, button):
        if button == self.openButton:
            default = MainUI().LOAD_DATA_DIR
            filename, filetype = QFileDialog.getOpenFileName(
                self, 'Load Data', default, 'py(*.py)')
            if osp.isfile(filename):
                with open(filename, 'r') as f:
                    self.textEdit.setText(f.read().strip())
        elif button == self.saveButton:
            default = datetime.datetime.now().__format__('%Y-%m-%d__%H-%M-%S')+'.py'
            default = osp.join(MainUI().LOAD_DATA_DIR, default)
            os.makedirs(osp.dirname(default), exist_ok=True)
            filename, filetype = QFileDialog.getSaveFileName(self, 'Select File Path', default, 'py(*.py)')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.textEdit.toPlainText().strip())
            self.close()
        elif button == self.closeButton:
            code_str = self.textEdit.toPlainText().strip()
            self.fileBlock.loadDataCode = code_str
            funcs = {}
            exec(compile(code_str, '', 'exec'), funcs)
            self.fileBlock.loadDataFuncs = funcs
            self.fileBlock.readImage()
            self.close()