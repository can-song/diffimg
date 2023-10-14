#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    
    Created on 2021/12/04 17:10:03
    @Author: songcan
    @Email: songcan@sensetime.com
    @Version: 1.0
"""

from PIL import Image
import numpy as np
from PySide6.QtWidgets import QApplication, QGraphicsPolygonItem, QMessageBox, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QMenu
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot, Qt, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPolygonF, QPainter, QAction
from pathlib import Path
from PySide6.QtGui import QIcon, QKeySequence


import res.diffimg
from .file_dialog import FileDialog, FileBlock

class Scene(QGraphicsScene):
    def __init__(self):
        super(Scene, self).__init__()
        self.fileDialog = FileDialog()
        for fileBlock in self.fileDialog.fileGroupBox.fileBlocks():
            self.addItem(fileBlock.pixmapItem)
        self.fileDialog.fileGroupBox.addItemSignal.connect(self.addPixmapItem)
        # self.fileDialog.fileGroupBox.fileBlocks()[0].
        # self.items = []

    def dragMoveEvent(self, event):
        event.accept()
        
    def mouseDoubleClickEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.fileDialog.show()

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            # print(mimeData.urls())
            fn = mimeData.urls()[0].toLocalFile()
            fn = Path(fn)
            if fn.is_file():
                self.fileDialog.setPath(fn, 0)
        else:
            event.ignore()

    @Slot()
    def addPixmapItem(self, fileBlock:FileBlock):
        self.addItem(fileBlock.pixmapItem)
    
    
    
    # TODO:
    # @SLOT()
    # def delPixmapItem(self, fileBlock):
    #     self.delItem()
