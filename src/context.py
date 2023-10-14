#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    
    Created on 2021/12/05 21:56:09
    @Author: songcan
    @Email: songcan@sensetime.com
    @Version: 1.0
"""

import os
import os.path as osp
import time
from PySide6.QtWidgets import QApplication, QGraphicsPolygonItem, QMessageBox, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, Signal, Slot, QEvent, QObject
from PySide6.QtGui import QCursor, QPixmap, QImage, QPen, QColor, QPolygonF, \
    QPainter, QFont, QFontMetricsF
from pathlib import Path
from PySide6.QtGui import QIcon, QKeySequence 

import numpy as np
from easydict import EasyDict as EDict
import utm
import sys

class History(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.data = {}
            return cls._instance
    def __init__(self, *args, **kwargs):
        ...
    
    def addItem(self, record:str):
        if len(self.data) > 200:
            self.data = {key:val for key, val in self.items()[:100]}
        if osp.isdir(record) or osp.isfile(record):
            self.data[record] = time.time()
    
    def items(self):
        return sorted(self.data.items(), key=lambda x: x[1], reverse=True)

class FileList(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            instance.fileList = []
            instance.index = []
            # instance.mode = 'random'
            instance._currentIndex = 0
            instance._mode = 'inturn'
            instance._listMode = 'normal'
            # instance.steps = 1
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        ...
    
    def getFilelist(self):
        return self._fileList
    def setFilelist(self, fileList):
        self._fileList = fileList
    fileList = property(getFilelist, setFilelist)
    
    def getMode(self):
        return self._mode
    def setMode(self, mode='inturn'):
        self._mode = mode
    mode = property(getMode, setMode)
    
    def getListMode(self):
        return self._listMode
    def setListMode(self, mode='inturn'):
        self._listMode = mode
    listMode = property(getListMode, setListMode)
    
    def getCurrentIndex(self):
        return self._currentIndex
    def setCurrentIndex(self, index):
        self._currentIndex = index
    currentIndex = property(getCurrentIndex, setCurrentIndex)

    def next(self):
        if self.mode == 'inturn':
            return self.fileList[
                (self.currentIndex+self.steps)%len(self.fileList)]
        else:
            raise NotImplementedError
        

class ReferenceFileBlock(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            instance._fileBlock = None
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        ...
    
    def getFileBlock(self):
        return self._fileBlock
    def setFileBlock(self, fileBlock):
        self._fileBlock = fileBlock
    fileBlock = property(getFileBlock, setFileBlock)

class MouseTrack(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            instance.points = []
            instance.drawing = False
            instance.current_point = None
            instance.showVertex = False
            instance._showClassName = False
            instance.showEdge = False
            instance.showArea = False
            instance.areaState = {}
            instance.edgeState = {}
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        ...
    def _getShowClassName(self):
        return self._showClassName
    def _setShowClassName(self, showClassName=True):
        self._showClassName = showClassName
    showClassName = property(_getShowClassName, _setShowClassName)
    
    @property
    def area(self):
        return self.areaState.get('area', 0)
    
    @property
    def center(self):
        return self.areaState.get('center', None)
    
    @property
    def edge(self):
        return self.edgeState
    
    def updateArea(self):
        from shapely.geometry import Polygon
        points = [[pos.x(), pos.y()] for pos in self.points]
        if len(points) >= 3:
            polygon = Polygon(points)
            self.areaState['area'] = polygon.area
            pos = np.mean(np.asarray(polygon.exterior.coords[:-1]), axis=0)
            self.areaState['center'] = pos
        else:
            self.areaState['area'] = 0
            self.areaState['center'] = None
    
    def updateEdge(self):
        edgeState = []
        for pos1, pos2 in zip(self.points, self.points[1:]):
            dx, dy = (pos2-pos1).x(), -(pos2-pos1).y()
            degree=np.rad2deg(np.arctan2(dy, dx))
            a = -degree % 180
            # ds = ReferenceFileBlock().fileBlock.ds
            edgeState.append(EDict(
                pos1=pos1,
                pos2=pos2,
                center=(pos1+pos2)*0.5,
                length=np.linalg.norm((dx, dy)),
                degree=degree,
                a=a if a < 90 else a-180
            ))
        self.edgeState = edgeState

    def start_drawing(self):
        self.drawing = True
    
    def stop_drawing(self):
        self.drawing = False
    
    def add_point(self, point):
        self.points.append(point)
        self.updateArea()
        self.updateEdge()
    
    def del_point(self):
        if self.points:
            self.points = self.points[:-1]
        self.start_drawing()
        self.updateArea()
        self.updateEdge()

    def clear_all(self):
        self.points = []
        self.drawing = False
        self.current_point = None
        self.updateArea()
        self.updateEdge()

    def clear_last(self):
        if len(self.points):
            self.points = self.points[:-1]
        self.drawing = False
        self.current_point = None
        self.updateArea()
        self.updateEdge()
        
class ToolBar(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        pass
    
    def set(self, key, val):
        setattr(self, key, val)
    
    def get(self, key):
        return getattr(self, key, None)
    
# class Reference(QObject):
#     _instance = None
#     def __new__(cls, *args, **kwargs):
#         if cls._instance:
#             return cls._instance
#         else:
#             instance = super().__new__(cls, *args, **kwargs)
#             instance.basenameLineEdit = None
#             instance.referenceLineEdit = None
#             cls._instance = instance
#             return cls._instance

class SyncSignal(QObject):
    syncPanelSignal = Signal(QObject, QEvent)
    mouseMovedSignal = Signal(QObject, QPointF)
    wheelSlideSignal = Signal(QObject, QEvent)
    updateViewportSignal = Signal()
    updateImageSignal = Signal()
    updateReferenceFilenameSignal = Signal()
    updatePernulnameSignal = Signal(str)
    updateFilenameSignal = Signal()
    fitInViewSignal = Signal()
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

class Sync(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            instance._syncSignal = SyncSignal()
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        pass
    
    @property
    def syncSignal(self)->SyncSignal:
        return self._syncSignal

class MainUI(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        else:
            instance = super().__new__(cls, *args, **kwargs)
            instance._mainWindow = None
            instance._gridView = None
            instance._showFilenames = False
            cls._instance = instance
            return cls._instance
    def __init__(self) -> None:
        ...
    def _get_mainWindow(self):
        return self._mainWindow
    def _set_mainWindow(self, mainWindow):
        self._mainWindow = mainWindow
    mainWindow = property(_get_mainWindow, _set_mainWindow)
    
    def _get_gridView(self):
        return self._gridView
    def _set_gridView(self, gridView):
        self._gridView = gridView
    gridView = property(_get_gridView, _set_gridView)
    
    def _get_showFilenames(self):
        return self._showFilenames
    def _set_showFilenames(self, showFilenames:bool):
        self._showFilenames = showFilenames
    showFilenames = property(_get_showFilenames, _set_showFilenames)
    
    @property
    def HOME_DIR(self):
        return osp.join(os.path.expanduser('~'), 'diffimg')
    
    @property
    def LOAD_DATA_DIR(self):
        return osp.join(self.HOME_DIR, 'load_data')
    
    @property
    def VIEW_DIR(self):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return base_path

if __name__ == '__main__':
    x = History()
    x.addItem('1')
    time.sleep(1)
    x.addItem('2')
    time.sleep(1)
    x.addItem('3')
    print(x.items())
    print(type(x))