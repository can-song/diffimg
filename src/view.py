import os
from PIL import Image
import numpy as np
from PySide6.QtWidgets import QApplication, QGraphicsPolygonItem, QMessageBox, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, QPoint, Signal, Slot, QEvent, QRect
from PySide6.QtGui import QCursor, QPixmap, QImage, QPen, QColor, QPolygonF, \
    QPainter, QFont, QFontMetricsF
from PySide6.QtGui import QIcon, QKeySequence, QTextOption 
from pathlib import Path

import res.diffimg
from src.scene import Scene
from .context import MainUI, MouseTrack, ReferenceFileBlock, ToolBar, Sync

class View(QGraphicsView):
    syncPanelSignal = Signal(QEvent)
    mouseMovedSignal = Signal(QPointF)
    wheelSlideSignal = Signal(QEvent)
    drawPolygonSignal = Signal()
    def __init__(self, parent):
        super(View, self).__init__(parent)
        # self.setAcceptDrops(True)
        # self.setToolTip("可拖入图片！")
        # 设置无边框
        # self.setStyleSheet("background: transparent; padding: 0px; border: 0px;")
        self.setMouseTracking(True)
        # close scroll bar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setAlignment(Qt.AlignCenter)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # self.setDragMode(QGraphicsView.NoDrag)
        # because artifact (view rect diff scene rect !!)
        # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # 设置橡皮经框选区域
        # self.setDragMode(QGraphicsView.RubberBandDrag)
        # self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setAcceptDrops(True)
        
        self.setScene(Scene())
        self.filenames = []
        self.markerPos = None
        
        sync = Sync()
        sync.syncSignal.syncPanelSignal.connect(self.syncPanel)
        sync.syncSignal.mouseMovedSignal.connect(self.setMarkerPos)
        sync.syncSignal.wheelSlideSignal.connect(self.syncWheel)
        sync.syncSignal.updateViewportSignal.connect(self.updateViewport)
        sync.syncSignal.fitInViewSignal.connect(self._fitInView)
        self.drawPolygonSignal.connect(self.drawPolygon)
    
    @Slot()
    def _fitInView(self):
        ds = ReferenceFileBlock().fileBlock.ds
        if ds is None:
            return
        rect = QRect(0, 0, ds.width, ds.height)
        self.setSceneRect(rect)
        self.setAlignment(Qt.AlignCenter)
        self.fitInView(rect, Qt.KeepAspectRatio)
        self.centerOn(ds.width/2, ds.height/2)
        self.viewport().update()
        # self.update()
    
    @property
    def fileBlocks(self):
        return self.scene().fileDialog.fileGroupBox.fileBlocks()

    @property
    def tileBg(self):
        tileBg = QPixmap(16, 16)
        tileBg.fill(Qt.white)
        painter = QPainter(tileBg)
        color = QColor(202, 202, 202)
        painter.fillRect(0, 0, 8, 8, color)
        painter.fillRect(8, 8, 8, 8, color)
        painter.end()
        return tileBg
    
    def drawBg(self):
        painter = QPainter(self.viewport())
        painter.drawTiledPixmap(self.rect(), self.tileBg)
        painter.end()
    
    def paintEvent(self, event):
        self.drawBg()
        super().paintEvent(event)
        
        if self.markerPos and self.scene().height():
            self.drawMarker(self.markerPos)
        self.drawPolygonSignal.emit()
        self.drawPoint()
        self.drawFilenames()
        self.drawClassName()
        
    def dragEnterEvent(self, event) -> None:
        # mimeData = event.mimeData()
        if event.mimeData().hasUrls():
            # event.accept()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            factor = 1.2
        else:
            factor = 1 / 1.2
        self.scale(factor, factor)
        self.update()
        Sync().syncSignal.wheelSlideSignal.emit(self, event)
        # self.wheelSlideSignal.emit(event)
    
    @Slot()
    def syncWheel(self, view, event):
        # sender = self.sender()
        if view != self:
            self.setTransform(view.transform())
            # self.scale(sender.transform().m11()/self.transform().m11(),
            #            sender.transform().m22()/self.transform().m22())
            self.centerOn(view.mapToScene(view.rect().center()))
            # self.viewport().update()
            self.update()
    
    @Slot()
    def syncPanel(self, view, event):
        if view != self:
            self.centerOn(view.mapToScene(view.rect().center()))
    
    def draw(self):
        pen = QPen()
        pen.setColor(QColor(255, 0, 0))
        pen.setWidth(10)
        polygon_item = QGraphicsPolygonItem()
        polygon = QPolygonF()
        polygon.append(QPointF(-100.0, -400.0))
        polygon.append(QPointF(100.0, -400.0))
        polygon.append(QPointF(200.0, 400.0))
        polygon.append(QPointF(0.0, 400))
        polygon_item.setPolygon(polygon)
        polygon_item.setPen(pen)
        polygon_item.setFlag(QGraphicsItem.ItemIsMovable)
        self.scene().addItem(polygon_item)
        self.show()
        
    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        self.markerPos = None
        self.viewport().update()
        pos = self.mapToScene(event.pos())
        Sync().syncSignal.mouseMovedSignal.emit(self, pos)
        if event.buttons() == Qt.LeftButton:
            Sync().syncSignal.syncPanelSignal.emit(self, event)
            
        mouseTrack = MouseTrack()
        mouseTrack.current_point = pos
    
    @Slot()
    def setMarkerPos(self, view, pos):
        if view != self:
            self.markerPos = self.mapFromScene(pos)
            self.viewport().update()
    
    def drawText(self, pos, color, s, a:float=0):
        painter = QPainter(self.viewport())
        # font = QFont("宋体", 15)
        font = QFont("Microsoft YaHei", 20)
        painter.setFont(font)
        painter.setPen(color)
        painter.translate(pos)
        painter.rotate(a)
        rect = QFontMetricsF(font).tightBoundingRect(s)
        painter.translate(-rect.width()*0.5, -3)
        painter.drawText(0, 0, s)
        painter.resetTransform()
    
    def drawLine(self, point1, point2, width, color, dash=False):
        painter = QPainter(self.viewport())
        pen = QPen()
        pen.setWidthF(width)
        pen.setColor(color)
        if dash:
            pen.setDashPattern([4, 4])
        painter.setPen(pen)
        painter.drawLine(point1, point2)
        painter.end()
    
    def drawCross(self, center:QPointF, 
                  width:float, color:QColor, markerSize=10):
        
        self.drawLine(QPointF(center.x() - markerSize, center.y()),
                      QPointF(center.x() - markerSize/2, center.y()),
                      width, color)
        
        self.drawLine(QPointF(center.x() + markerSize/2, center.y()),
                      QPointF(center.x() + markerSize, center.y()),
                      width, color)
        self.drawLine(QPointF(center.x(), center.y() - markerSize),
                      QPointF(center.x(), center.y() - markerSize/2),
                      width, color)
        self.drawLine(QPointF(center.x(), center.y() + markerSize/2),
                      QPointF(center.x(), center.y() + markerSize),
                      width, color)

    def drawMarker(self, pos):
        self.drawCross(pos, 3.0, QColor(255, 255, 255, 255))
        self.drawCross(pos, 2.0, QColor(50, 50, 50, 255))

    def contextMenuEvent(self, event) -> None:
        pos = self.mapToScene(event.pos())
        
        mouseTrack = MouseTrack()
        if not mouseTrack.drawing:
            mouseTrack.start_drawing()
        mouseTrack.add_point(pos)
        return super().contextMenuEvent(event)
    
    def mousePressEvent(self, event) -> None:
        # ctrl = event.modifiers() & Qt.ControlModifier
        if event.modifiers() == Qt.ControlModifier:
            if event.buttons() == Qt.MiddleButton:
                mouseTrack = MouseTrack()
                mouseTrack.clear_all()
        else:
            if event.buttons() == Qt.MiddleButton:
                mouseTrack = MouseTrack()
                if mouseTrack.drawing:
                    mouseTrack.add_point(mouseTrack.points[0])
                    mouseTrack.stop_drawing()
                else:
                    mouseTrack.clear_all()
        return super().mousePressEvent(event)
    
    @Slot()
    def updateViewport(self):
        self.viewport().update()

    def keyPressEvent(self, event) -> None:
        mouseTrack = MouseTrack()
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                mouseTrack.del_point()
        else:
            if event.key() == Qt.Key_V:
                mouseTrack.showVertex = ~mouseTrack.showVertex
                Sync().syncSignal.updateViewportSignal.emit()
            elif event.key() == Qt.Key_E:
                mouseTrack.showEdge = ~mouseTrack.showEdge
                mouseTrack.showArea = ~mouseTrack.showArea
                Sync().syncSignal.updateViewportSignal.emit()
            elif event.key() == Qt.Key_C:
                mouseTrack.showClassName = True
                Sync().syncSignal.updateViewportSignal.emit()
            elif event.key() == Qt.Key_QuoteLeft:
                # MainUI().showFilenames = ~MainUI().showFilenames
                MainUI().showFilenames = True
                Sync().syncSignal.updateViewportSignal.emit()
            # elif event.key() == Qt.Key_S:
            #     screen = QApplication.primaryScreen()
            #     pixmap = screen.grabWindow(0)
            #     clipboard = QApplication.clipboard()
            #     clipboard.clear()
            #     # clipboard.setText(ToolBar().get('basename').text())
            #     toolBar = MainUI().mainWindow.ui.toolBar
            #     leftTop = toolBar.mapToGlobal(QPoint(0, 0))
            #     gridView = MainUI().gridView
            #     rightBottom = gridView.mapToGlobal(
            #         QPoint(gridView.width(), gridView.height()))
            #     clipboard.setPixmap(pixmap.copy(
            #         QRect(leftTop, rightBottom)))
                
        return super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_QuoteLeft:
            MainUI().showFilenames = False
            Sync().syncSignal.updateViewportSignal.emit()
        elif event.key() == Qt.Key_C:
            MouseTrack().showClassName = False
            Sync().syncSignal.updateViewportSignal.emit()
        return super().keyReleaseEvent(event)
    
    @Slot()
    def drawPolygon(self):
        if not self.scene().height():
            return
        mouseTrack = MouseTrack()
        if not mouseTrack.points:
            return
        color = QColor(255, 0, 255, 255)
        toolBar = ToolBar()
        reso = toolBar.get('resolution').value()

        edges = mouseTrack.edge
        if len(edges)==2:
            e1, e2 = edges
            if e1.pos1 == e2.pos2:
                edges = edges[:-1]
        for e in edges:
            pos1, pos2 = self.mapFromScene(e.pos1), self.mapFromScene(e.pos2)
            self.drawLine(pos1, pos2, 2.0, color)
            if mouseTrack.showEdge:
                pos = self.mapFromScene(e.center)
                self.drawText(pos, color,
                              f"{e.length:0.0f}px:{e.length*reso:0.2f}m:{e.degree:0.0f}°",
                              a=e.a)
            
        if mouseTrack.drawing:
            pos1 = self.mapFromScene(mouseTrack.points[-1])
            pos2 = self.mapFromScene(mouseTrack.current_point)
            self.drawLine(pos1, pos2, 2.0, color, True)
        
        if mouseTrack.showArea and mouseTrack.area>0:
            if len(mouseTrack.points) >= 3:
                self.drawText(self.mapFromScene(QPointF(*mouseTrack.center)), 
                              QColor(255, 0, 255, 255),
                              f"{mouseTrack.area * reso**2:0.2f}m²")
    
    def drawPoint(self):
        if not self.scene().height():
            return
        mouseTrack = MouseTrack()
        toolBar = ToolBar()
        pos = mouseTrack.current_point
        if pos is not None and mouseTrack.showVertex:
            toolBar.get('coords').setText(f"({pos.x():0.0f},{pos.y():0.0f})")
            pixel = self.scene().fileDialog.fileGroupBox.fileBlocks(
                    )[0].data[np.round(pos.y()).astype(np.int64), 
                              np.round(pos.x()).astype(np.int64)]
            if isinstance(pixel, np.ndarray):
                pixel = tuple(pixel)
            else:
                pixel = (pixel,)
            self.drawText(self.mapFromScene(pos), QColor(255, 0, 255, 255), #Qt.red,
                              f"{pixel}")
    
    def drawClassName(self):
        if not self.scene().height():
            return
        mouseTrack = MouseTrack()
        if not mouseTrack.showClassName:
            return
        pos = mouseTrack.current_point
        if pos is not None and mouseTrack.showClassName:
            info = []
            for fileBlock in self.fileBlocks:
                cls_names = fileBlock.loadDataFuncs.get('class_names', None)
                if cls_names:
                    value = fileBlock.data[
                        np.round(pos.y()).astype(np.int64), 
                        np.round(pos.x()).astype(np.int64)]
                    if 0<=value<len(cls_names):
                        cls_name = cls_names[value]
                        info.append(cls_name)
            if info:
                info = ':'.join(info)
                self.drawText(self.mapFromScene(pos), 
                              Qt.red, #QColor(*np.random.randint(0, 256, 3)),
                              f"{info}")

    def drawFilenames(self):
        if not self.scene().height():
            return
        if MainUI().showFilenames:
            text = self.fileBlocks[0].fileLineEdit.text()
            color = QColor(255, 0, 255, 255)
            painter = QPainter(self.viewport())
            font = QFont("Microsoft YaHei", 15)
            painter.setFont(font)
            painter.setPen(color)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
            text = text.replace(os.sep, '\n')
            painter.drawText(
                self.rect(), Qt.AlignCenter | Qt.AlignJustify, text)