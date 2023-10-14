#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    
    Created on 2021/11/28 16:29:54
    @Author: songcan
    @Email: songcan@sensetime.com
    @Version: 1.0
"""

from PIL import Image
import numpy as np
from PySide6.QtWidgets import QApplication, QGraphicsPolygonItem, QMessageBox, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPolygonF, QPainter
from pathlib import Path
from PySide6.QtGui import QIcon, QKeySequence


import res.diffimg
from src.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    import datetime
    app.exec()