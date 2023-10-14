#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    
    Created on 2021/12/04 17:11:13
    @Author: songcan
    @Email: songcan@sensetime.com
    @Version: 1.0
"""

import os
import sys
from PIL import Image
import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPolygonItem,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QSpinBox,
    QWidget,
    QSizePolicy,
    QGridLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QDoubleSpinBox,
    QLabel,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, QPoint, Signal, Slot, QRectF, QRect, QObject
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPolygonF, QPainter
from pathlib import Path
from PySide6.QtGui import QIcon, QKeySequence


from res import diffimg
from src.view import View
from .context import FileList, MouseTrack, ReferenceFileBlock, ToolBar, MainUI, Sync
from .windows import *


class GridView(QWidget):
    def __init__(self, rowCount=1, columnCount=1):
        super(GridView, self).__init__()
        self._rows = rowCount
        self._columns = columnCount
        self.layout = QGridLayout(self)
        self._init_view()
        mainUI = MainUI()
        if mainUI.gridView is None:
            mainUI.gridView = self

    def _init_view(self):
        for r in range(self._rows):
            for c in range(self._columns):
                self.layout.addWidget(View(self), r, c, 1, 1)

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return self._columns

    def addRow(self):
        r = self.rowCount()
        for c in range(self.columnCount()):
            view = View(self)
            self.layout.addWidget(view, r, c, 1, 1)
        self._rows += 1
        # self.connectMouse()

    def addColumn(self):
        c = self.columnCount()
        for r in range(self.rowCount()):
            self.layout.addWidget(View(self), r, c, 1, 1)
        self._columns += 1
        # self.connectMouse()

    def delRow(self):
        r = self.rowCount() - 1
        for c in reversed(range(self.columnCount())):
            view = self.layout.itemAtPosition(r, c).widget()
            if view:
                view.setParent(None)
                self.layout.removeWidget(view)
                view.deleteLater()
        self._rows -= 1
        # self.connectMouse()

    def delColumn(self):
        c = self.columnCount() - 1
        for r in reversed(range(self.rowCount())):
            view = self.layout.itemAtPosition(r, c).widget()
            if view:
                view.setParent(None)
                self.layout.removeWidget(view)
                view.deleteLater()
        self._columns -= 1
        # self.connectMouse()

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return self._columns

    def views(self):
        for c in range(self.columnCount()):
            for r in range(self.rowCount()):
                yield self.layout.itemAtPosition(r, c).widget()

    def itemAt(self, r, c):
        return self.layout.itemAtPosition(r, c).widget()

    # def keyPressEvent(self, event) -> None:
    #     if event.key() == Qt.Key_QuoteLeft:
    #         MainUI().showFilenames = True
    #     return super().keyPressEvent(event)

    # def keyReleaseEvent(self, event) -> None:
    #     if event.key() == Qt.Key_QuoteLeft:
    #         MainUI().showFilenames = False
    #     return super().keyReleaseEvent(event)


class MainWindow(QObject):
    # refreshImageSignal = Signal()
    def __init__(self):
        self.ui = QUiLoader().load(self.get_ui_path("ui/viewer.ui"))
        # self.ui = QUiLoader().load(self.get_ui_path("viewer.ui"))
        mainUI = MainUI()
        if mainUI.mainWindow is None:
            mainUI.mainWindow = self
        self._createMenuBar()
        self._init_toolbar()

        self.gridView = GridView(self.rowSpinBox.value(), self.columnSpinBox.value())
        self.ui.setCentralWidget(self.gridView)
        self.ui.showMaximized()

    def get_ui_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def reset_views(self):
        for view in self.gridView.views():
            view.resetTransform()
        # self.update_filename()
        # self.updateBasename()
        Sync().syncSignal.updateImageSignal.emit()

    def updateFilenames(self):
        fileList = FileList()
        if not len(fileList.fileList):
            referenceFileBlock = ReferenceFileBlock()
            referenceFileBlock.fileBlock.updateFileList()
            if not len(fileList.fileList):
                return
        filename = fileList.fileList[fileList.currentIndex % len(fileList.fileList)]
        for view in self.gridView.views():
            for fileBlock in view.scene().fileDialog.fileGroupBox.fileBlocks():
                fn = Path(fileBlock.fileLineEdit.text())
                if fn.name:
                    fileBlock.fileLineEdit.setText(str(fn.with_stem(filename)))
        self.fitInView()

    def fitInView(self):
        return
        for view in self.gridView.views():
            view.resetTransform()
            data = view.scene().fileDialog.fileGroupBox.fileBlocks()[0].data
            if data is not None:
                # L = max(data.shape[:2])
                # view.fitInView(view.sceneRect())
                # view.fitInView()
                H, W = data.shape[:2]
                view.fitInView(QRectF(0, 0, W, H), Qt.KeepAspectRatio)
                view.centerOn(W / 2, H / 2)
                view.update()
                # view.setAlignment(Qt.AlignCenter)

    def updatePernultimateDirName(self):
        toolBar = ToolBar()
        pernul_name = toolBar.get("pernul_name").text().strip()
        
        # refFileBLock = ReferenceFileBlock()
        # cur_path = refFileBLock.fileBlock.fileLineEdit.text()
        # new_path = cur_path.split(osp.sep)
        # new_path[-3] = pernul_name
        # new_path = '/'.join(new_path)
        # refFileBLock.fileBlock.fileLineEdit.setText(new_path)
        # refFileBLock.fileBlock.updateFileList()
        
        MouseTrack().clear_all()
        Sync().syncSignal.updatePernulnameSignal.emit(pernul_name)

    def updateBasename(self):
        toolBar = ToolBar()
        basename = toolBar.get("basename").text().strip()
        fileList = FileList()
        try:
            index = fileList.fileList.index(basename)
        except ValueError:
            index = -1
            fileList.fileList.append(basename)
        fileList.currentIndex = index
        MouseTrack().clear_all()
        Sync().syncSignal.updateReferenceFilenameSignal.emit()

    @Slot()
    def clickNext(self):
        fileList = FileList()
        steps = ToolBar().get("step").value()
        fileList.currentIndex += steps
        MouseTrack().clear_all()
        # self.updateFilenames()
        # Sync().syncSignal.updateFilenameSignal.emit()
        Sync().syncSignal.updateReferenceFilenameSignal.emit()
        # self.fitInView()

    @Slot()
    def clickPrev(self):
        fileList = FileList()
        steps = ToolBar().get("step").value()
        fileList.currentIndex -= steps
        MouseTrack().clear_all()
        # self.updateFilenames()
        # Sync().syncSignal.updateFilenameSignal.emit()
        Sync().syncSignal.updateReferenceFilenameSignal.emit()
        # self.fitInView()

    @Slot()
    def loadFileList(self):
        win = LoadFileListWindow()
        win.show()

    @Slot()
    def loadFilenames(self):
        win = LoadFilenamesWindow(self)
        win.show()

    @Slot()
    def exportFilenames(self):
        win = ExportFilenamesWindow(self)
        win.show()

    @Slot()
    def snapshot(self):
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        clipboard = QApplication.clipboard()
        clipboard.clear()
        # clipboard.setText(ToolBar().get('basename').text())
        toolBar = MainUI().mainWindow.ui.toolBar
        leftTop = toolBar.mapToGlobal(QPoint(0, 0))
        gridView = MainUI().gridView
        rightBottom = gridView.mapToGlobal(QPoint(gridView.width(), gridView.height()))
        clipboard.setPixmap(pixmap.copy(QRect(leftTop, rightBottom)))

    def _createMenuBar(self):
        menuFile = self.ui.menuFile
        loadAction = menuFile.addAction("Load File List")
        loadAction.triggered.connect(self.loadFileList)

        loadAction = menuFile.addAction("Load Filenames")
        loadAction.triggered.connect(self.loadFilenames)

        loadAction = menuFile.addAction("Export Filenames")
        loadAction.triggered.connect(self.exportFilenames)
        # loadAction = menuFile.addAction('Save Filenames')
        # loadAction.triggered.connect(self.saveFilenames)
        # ...
        # self.loadFileListTextEdit = QTextEdit(menuFile)
        # self.loadFileListTextEdit.setText("File List")
        # self.loadFileList =
        # loadFileListMenu.add

    def _init_toolbar(self):
        toolBar = ToolBar()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ui.toolBar.addWidget(spacer)

        # pernultimate dir name
        pernul_name = QLineEdit(self.ui.toolBar)
        pernul_name.setPlaceholderText("pernultimate dir name")
        pernul_name.setFixedWidth(240)
        pernul_name.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.ui.toolBar.addWidget(pernul_name)
        toolBar.set("pernul_name", pernul_name)
        pernul_name.editingFinished.connect(self.updatePernultimateDirName)

        # basename
        basename = QLineEdit(self.ui.toolBar)
        basename.setPlaceholderText("basename")
        # basename.setMinimumWidth(240)
        basename.setFixedWidth(240)
        basename.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.ui.toolBar.addWidget(basename)
        toolBar.set("basename", basename)
        basename.editingFinished.connect(self.updateBasename)

        # coords = QLabel(self.ui.toolBar)
        coords = QLineEdit(self.ui.toolBar)
        coords.setReadOnly(True)
        # coords.setMinimumWidth(40)
        coords.setFixedWidth(80)
        coords.setAlignment(Qt.AlignCenter)
        self.ui.toolBar.addWidget(coords)
        coords.setText("(0, 0)")
        coords.show()
        toolBar.set("coords", coords)

        resolution = QDoubleSpinBox(self.ui.toolBar)
        resolution.setMinimum(0)
        resolution.setSingleStep(1)
        resolution.setPrefix("resolution: ")
        resolution.setSuffix(" m/px")
        resolution.setDecimals(1)
        resolution.setValue(0.0)
        self.ui.toolBar.addWidget(resolution)
        toolBar.set("resolution", resolution)

        step = QSpinBox(self.ui.toolBar)
        step.setMinimum(1)
        step.setSingleStep(1)
        step.setPrefix("steps: ")
        step.setValue(1)
        self.stepSpinBox = step
        self.ui.toolBar.addWidget(step)
        toolBar.set("step", step)

        # spacer = QWidget()
        # spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.ui.toolBar.addWidget(spacer)

        row = QSpinBox()
        row.setRange(1, 8)
        row.setSingleStep(1)
        row.setPrefix("rows:  ")
        row.setValue(2)
        row.setAlignment(Qt.AlignCenter)
        row.setMinimumWidth(90)
        self.rowSpinBox = row
        self.rowSpinBox.valueChanged.connect(self.change_row)
        self.ui.toolBar.addWidget(self.rowSpinBox)
        toolBar.set("row", row)

        column = QSpinBox()
        column.setRange(1, 8)
        column.setSingleStep(1)
        column.setPrefix("columns: ")
        column.setValue(3)
        column.setMinimumWidth(90)
        column.setAlignment(Qt.AlignCenter)
        self.columnSpinBox = column
        self.columnSpinBox.valueChanged.connect(self.change_column)
        self.ui.toolBar.addWidget(self.columnSpinBox)
        toolBar.set("column", column)

        for action in [
            "actionColumn",
            "actionEdit",
            "actionFitToWindow",
            "actionFullResolution",
            "actionNext",
            "actionOpen",
            "actionPrev",
            "actionQuit",
            "actionRefresh",
            "actionRow",
            "actionSave",
        ]:
            toolBar.set(action, getattr(self.ui, action))
        for action in [
            "actionColumn",
            "actionEdit",
            "actionFitToWindow",
            "actionFullResolution",
            "actionQuit",
            "actionRow",
        ]:
            getattr(self.ui, action).setVisible(False)

        getattr(self.ui, "actionPrev").setShortcuts(
            [QKeySequence(Qt.Key_A), QKeySequence(Qt.Key_Left)]
        )
        self.ui.actionPrev.triggered.connect(self.clickPrev)
        getattr(self.ui, "actionNext").setShortcuts(
            [QKeySequence(Qt.Key_D), QKeySequence(Qt.Key_Right)]
        )
        self.ui.actionNext.triggered.connect(self.clickNext)
        getattr(self.ui, "actionRefresh").setShortcuts([QKeySequence(Qt.Key_R)])
        self.ui.actionRefresh.triggered.connect(self.reset_views)
        self.ui.actionOpen.triggered.connect(self.loadFilenames)
        self.ui.actionSave.triggered.connect(self.exportFilenames)
        self.ui.actionLoadFilelist.triggered.connect(self.loadFileList)
        self.ui.actionSnapshot.triggered.connect(self.snapshot)

    def change_row(self):
        ori_rows, new_rows = self.gridView.rowCount(), self.rowSpinBox.value()
        if ori_rows < new_rows:
            for _ in range(new_rows - ori_rows):
                self.gridView.addRow()
        else:
            for _ in range(ori_rows - new_rows):
                self.gridView.delRow()

    def change_column(self):
        ori_columns, new_columns = (
            self.gridView.columnCount(),
            self.columnSpinBox.value(),
        )
        if ori_columns < new_columns:
            for _ in range(new_columns - ori_columns):
                self.gridView.addColumn()
        else:
            for _ in range(ori_columns - new_columns):
                self.gridView.delColumn()

    def views(self):
        return self.gridView.views()

    # @Slot()
    # def syncPanel(self):
    #     sender = self.sender()
    #     for view in self.view_items():
    #         if sender != view:
    #             view.setScale(sender.getScale())
    #             view.setCenter(sender.getCenter)
