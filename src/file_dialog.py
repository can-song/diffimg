#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    
    Created on 2021/12/05 11:10:39
    @Author: songcan
    @Email: songcan@sensetime.com
    @Version: 1.0
"""

from genericpath import isfile
import os
import os.path as osp
import threading
import numpy as np
from skimage.segmentation import find_boundaries
import geopandas as gpd

from PySide6.QtWidgets import (
    QDialog,
    QGraphicsPixmapItem,
    QSizePolicy,
    QWidget,
    QLabel,
    QGroupBox,
    QVBoxLayout,
    QRadioButton,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QMenu,
    QPushButton,
    QCompleter,
    QFileSystemModel,
    QSpinBox,
    QGraphicsPolygonItem,
    QGraphicsItem,
    QSpacerItem,
    QWidgetAction,
    QTreeView,
    QFileDialog,
    QTableWidgetSelectionRange,
    QColormap,
    QColorDialog,
)

from PySide6.QtCore import Qt, Slot, QStringListModel, Signal, QPointF, QEvent, QDir
from PySide6.QtGui import (
    QAction,
    QCursor,
    QPixmap,
    QImage,
    QPen,
    QColor,
    QPolygonF,
    QPainter,
    QDragEnterEvent,
    QDropEvent,
    QAction,
)
from pathlib import Path

# from cephlib import Path
# import cephlib as cl
import pathlib as pl
from skimage.io import imread
import rasterio as rio
from rasterio.features import rasterize
from rasterio.enums import Resampling

from .context import Sync

from .context import History, FileList, ReferenceFileBlock, ToolBar, MainUI
from .windows import CloneTableWindow, AdvancedSearchWindow, LoadDataWindow


class FileLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super(FileLineEdit, self).__init__(*args, **kwargs)
        self.setClearButtonEnabled(True)

        self.completer = QCompleter()
        self.setCompleter(self.completer)
        self.setAcceptDrops(True)
        # self.setAttribute(Qt.WA_InputMethodEnabled, False)

        self.textChanged.connect(self.updateHistory)
        self.textEdited.connect(self.pathComplete)
        self.textChanged.connect(self.updateBasename)

    @Slot()
    def updateBasename(self):
        referenceFileBLock = ReferenceFileBlock()
        if self.parent() == referenceFileBLock.fileBlock:
            basename = ToolBar().get("basename")
            basename.setText(Path(self.text()).stem)

    @Slot()
    def updateHistory(self):
        history = History()
        history.addItem(self.text())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
        # return super().dragEnterEvent(arg__1)

    def dropEvent(self, event: QDropEvent) -> None:
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            fn = mimeData.urls()[0].toLocalFile()
            self.setText(fn)

    def check(self, p):
        while not osp.isfile(p) and not osp.isdir(p):
            p = osp.dirname(p)
        return p

    def pathComplete(self):
        if self.text():
            text = self.text()
            d = self.check(text)
            if osp.isfile(d):
                candidates = [d]
            else:
                candidates = [osp.join(d, c) for c in os.listdir(d)]
                candidates1, candidates2 = [], []
                for c in candidates:
                    if c.startswith(text):
                        candidates1.append(c)
                    else:
                        candidates2.append(c)
                candidates1.sort()
                candidates2.sort()
                candidates = candidates1 + candidates2
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.completer.setModel(QStringListModel(candidates))
            self.completer.complete()
        else:
            self.showHistory()

    def showHistory(self):
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        history = History()
        content = [k for k, v in history.items()]
        self.completer.setModel(QStringListModel(content))
        self.completer.complete()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        text = self.text()
        if text:
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            start, end = self.selectionStart(), self.selectionEnd()
            if text[start - 1] != os.sep:
                start = text.rfind(os.sep, 0, start) + 1
                if start == -1:
                    return
            if end == len(text):
                return
            if text[end] != os.sep:
                end = text.find(os.sep, end)
                if end == -1:
                    return
            self.setSelection(start, end - start)
            # candidates = ['semantic_color', 'edge_color', 'orient_edge_color']
            candidates = os.listdir(text[:start])
            content = [text[:start] + _ + text[end:] for _ in candidates]
            self.completer.setModel(QStringListModel([self.check(c) for c in content]))
            # self.completer.setModel(QStringListModel(self.complete(content)))
            self.completer.complete()
        else:
            self.showHistory()


class ModeComboBox(QComboBox):
    def __init__(self):
        super(ModeComboBox, self).__init__()
        self.addItem("normal")
        self.addItem("index")
        self.addItem("fill")
        self.addItem("outline")
        self.addItem("custom")

    # def changeEvent(self, e) -> None:
    #     return super().changeEvent(e)

    # def mousePressEvent(self, e) -> None:
    #     return super().mousePressEvent(e)

    # def mouseReleaseEvent(self, e) -> None:
    #     return super().mousePressEvent(e)

    # def contextMenuEvent(self, e) -> None:
    #     return super().contextMenuEvent(e)


class FileComboBox(QComboBox):
    def __init__(self):
        super(FileComboBox, self).__init__()
        self.addItem("normal")
        self.addItem("fill")
        self.addItem("contour")
        self.setEditable(True)


class OpacityDoubleSpinBox(QDoubleSpinBox):
    def __init__(self):
        super(OpacityDoubleSpinBox, self).__init__()
        self.setRange(0, 100)
        self.setSingleStep(10)
        self.setPrefix("opacity: ")
        self.setValue(100)


class FileBlock(QWidget):
    """widget for the fileGroupBox. FileBlock contains buttons and a lineEdit. The buttons are to open a file, to clone a existing fileBlock"""

    setPixmapSignal = Signal()

    def __init__(self, *args, **kwargs):
        super(FileBlock, self).__init__(*args, **kwargs)
        referenceFileBlock = ReferenceFileBlock()
        if referenceFileBlock.fileBlock is None:
            referenceFileBlock.fileBlock = self
        self.mainLayout = QVBoxLayout(self)
        self.fileLineEdit = FileLineEdit(self)
        self.mainLayout.addWidget(self.fileLineEdit)
        self.fileLineEdit.textChanged.connect(self.readImage)
        self.setPixmapSignal.connect(self.setPixmap)

        self.layout2 = QHBoxLayout()
        self.mainLayout.addLayout(self.layout2)

        spacer = QSpacerItem(20, 20, hData=QSizePolicy.Expanding)
        self.layout2.addSpacerItem(spacer)

        self.showCheckBox = QCheckBox()
        self.showCheckBox.setCheckState(Qt.Checked)
        self.layout2.addWidget(self.showCheckBox)

        self.opacityDoubleSpinBox = OpacityDoubleSpinBox()
        self.layout2.addWidget(self.opacityDoubleSpinBox)
        self.opacityDoubleSpinBox.valueChanged.connect(self.setPixmap)

        self.modeComboBox = ModeComboBox()
        self.layout2.addWidget(self.modeComboBox)
        self.modeComboBox.currentTextChanged.connect(self.setPixmap)
        # self.modeComboBox.currentIndexChanged.connect(self.editLoadDataCode)
        self.modeComboBox.textActivated.connect(self.editLoadDataCode)

        self.selectColorButton = QPushButton(text="Color")
        self.selectColorButton.clicked.connect(self.selectColor)
        self.layout2.addWidget(self.selectColorButton)

        self.referButton = QPushButton(text="Reference")
        self.referButton.clicked.connect(self.updateFileList)
        self.layout2.addWidget(self.referButton)

        self.advanceButton = QPushButton(text="Advance")
        self.advanceButton.clicked.connect(self.advanceSearch)
        self.layout2.addWidget(self.advanceButton)
        self.advancedConfig = dict(
            mode="normal", prefix="", suffix="", replace=dict(old="", new="")
        )

        self.cloneButton = QPushButton(self, text="Clone")
        # self.cloneButton.clicked.connect(self.cloneFilename)
        self.cloneButton.released.connect(self.cloneFilename)
        # self.cloneButton = CloneButton(self, text='Clone')
        self.layout2.addWidget(self.cloneButton)

        self.openButton = QPushButton(self, text="Open")
        self.openButton.clicked.connect(self.openFile)
        self.layout2.addWidget(self.openButton)

        self.okButton = QPushButton(self, text="OK")
        self.okButton.clicked.connect(self.saveFile)
        self.layout2.addWidget(self.okButton)

        self.pixmapItem = QGraphicsPixmapItem()
        self.ds = None
        self.data = None
        self.loadDataCode = ""
        self.loadDataFuncs = {}
        self.attr = None
        self.gdf = None
        self.color = QColor(255, 0, 0, 255)
        palette = np.random.randint(64, 256, size=[253, 3]).tolist()
        self.palette = np.asarray(
            [[0, 0, 0]] + palette + [[255, 255, 255]], dtype=np.uint8
        )
        Sync().syncSignal.updateImageSignal.connect(self.readImage)

        Sync().syncSignal.updateReferenceFilenameSignal.connect(
            self.updateReferenceFilename
        )
        Sync().syncSignal.updatePernulnameSignal.connect(self.updatePernulname)
        Sync().syncSignal.updateFilenameSignal.connect(self.updateFilename)
        # self.pixmapItem = self.draw()
        # self.showSignal.connect(self.pixmapItem.show)

        # MainUI().mainWindow.refreshImageSignal.connect(self.readImage)

    @Slot()
    def editLoadDataCode(self):
        if self.modeComboBox.currentText() == "custom":
            self.parent().parent().hide()
            win = LoadDataWindow(self)
            win.show()

    @Slot()
    def updatePernulname(self, new_name):
        cur_path = self.fileLineEdit.text()
        new_path = cur_path.split(osp.sep)
        new_path[-3] = new_name
        # try:
        #     new_path[-3] = new_name
        # except:
        #     print()
        new_path = '/'.join(new_path)
        self.fileLineEdit.setText(new_path)
        self.updateFileList()
        # fileList = FileList()
        # if not fileList.fileList:
        #     ReferenceFileBlock().fileBlock.updateFileList()

    @Slot()
    def updateReferenceFilename(self):
        if not ReferenceFileBlock().fileBlock == self:
            return
        fileList = FileList()
        if not fileList.fileList:
            ReferenceFileBlock().fileBlock.updateFileList()

        if fileList.listMode == "normal":
            filename = fileList.fileList[fileList.currentIndex % len(fileList.fileList)]
            fn = Path(self.fileLineEdit.text())
            if fn.name:
                self.fileLineEdit.setText(str(fn.with_stem(filename)))
        elif fileList.listMode == "advance":
            filename = fileList.fileList[fileList.currentIndex % len(fileList.fileList)]
            if ("prefix" in self.advancedConfig) and ("suffix" in self.advancedConfig):
                prefix = self.advancedConfig["prefix"]
                if not prefix:
                    return
                suffix = self.advancedConfig["suffix"]
                fn = osp.join(prefix, filename)
                if "replace" in self.advancedConfig:
                    replace = self.advancedConfig["replace"]
                    if ("old" in replace) and ("new" in replace) and replace["old"]:
                        fn = fn.replace(replace["old"], replace["new"])
                        fn = Path(fn).with_suffix(suffix)
                if osp.isfile(fn) or Path(fn).root.startswith(os.sep):
                    self.fileLineEdit.setText(str(fn))

    @Slot()
    def updateFilename(self):
        if ReferenceFileBlock().fileBlock == self:
            return
        fileList = FileList()
        if not fileList.fileList:
            ReferenceFileBlock().fileBlock.updateFileList()
        if fileList.listMode == "normal":
            filename = fileList.fileList[fileList.currentIndex % len(fileList.fileList)]
            fn = Path(self.fileLineEdit.text())
            if fn.name:
                self.fileLineEdit.setText(str(fn.with_stem(filename)))
        elif fileList.listMode == "advance":
            filename = fileList.fileList[fileList.currentIndex % len(fileList.fileList)]
            if ("prefix" in self.advancedConfig) and ("suffix" in self.advancedConfig):
                prefix = self.advancedConfig["prefix"]
                if not prefix:
                    return
                suffix = self.advancedConfig["suffix"]
                fn = osp.join(prefix, filename)
                if "replace" in self.advancedConfig:
                    replace = self.advancedConfig["replace"]
                    if ("old" in replace) and ("new" in replace) and replace["old"]:
                        fn = fn.replace(replace["old"], replace["new"])
                        fn = Path(fn).with_suffix(suffix)
                if osp.isfile(fn) or Path(fn).root.startswith(os.sep):
                    self.fileLineEdit.setText(str(fn))

    @Slot()
    def advanceSearch(self):
        self.parent().parent().hide()
        win = AdvancedSearchWindow(self)
        win.show()

    @Slot()
    def selectColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color
            self.setPixmapSignal.emit()

    @Slot()
    def cloneFilename(self):
        # self.hide()
        self.parent().parent().hide()
        win = CloneTableWindow(self)
        win.show()
        # self.parent().show()

    @Slot()
    def saveFile(self):
        self.parent().parent().close()

    @Slot()
    def openFile(self):
        if self.fileLineEdit.text():
            d = self.fileLineEdit.text()
            d = self.fileLineEdit.check(d)
            if osp.isfile(d):
                d = osp.dirname(d)
            file, filetype = QFileDialog.getOpenFileName(
                self, "", d, "All Files (*);;Image Files (*.jpg)"
            )
        else:

            file, filetype = QFileDialog.getOpenFileName(
                self,
                "",
                QDir.rootPath(),
                "All Files (*);;Image Files (*.tif);;"
                "Image Files (*.jpg);;Image Files (*.png)",
            )
        if file:
            self.fileLineEdit.setText(file)

    @Slot()
    def updateFileList(self):
        # if ReferenceFileBlock().fileBlock == self:
        #     return
        referenceFileBlock = ReferenceFileBlock()
        referenceFileBlock.fileBlock = self
        fn = Path(self.fileLineEdit.text())
        fileList = FileList()
        if fileList.listMode == "normal":
            filenames = fn.parent.rglob(f"*{fn.suffix}")
            fileList.fileList = [fn.stem for fn in filenames]
        elif fileList.listMode == "advance":
            if ("prefix" not in self.advancedConfig) or (
                "suffix" not in self.advancedConfig
            ):
                return
            prefix = self.advancedConfig["prefix"]
            suffix = self.advancedConfig["suffix"]
            filenames = Path(prefix).rglob("*" + suffix)
            fileList.fileList = [fn.relative_to(prefix) for fn in filenames]
        self.updateFilename()
        self.parent().parent().close()

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
        return polygon_item

    def loadRaster(self, fn):
        if not osp.isfile(fn):
            self.ds = None
            self.data = None
            return
        with rio.open(fn) as ds:
            self.ds = ds
            referenceFileBlock = ReferenceFileBlock().fileBlock
            if referenceFileBlock == self:
                Sync().syncSignal.updateFilenameSignal.emit()
            if ds.crs is not None:
                if (
                    (referenceFileBlock == self)
                    or (referenceFileBlock.ds is None)
                    or (referenceFileBlock.ds.crs is None)
                ):
                    resolution = ToolBar().get("resolution")
                    if ds.crs.units_factor[0] == "metre":
                        res = ds.res[0]
                    elif ds.crs.units_factor[0] == "degree":
                        res = ds.res[0] * np.deg2rad(6371393)
                    else:
                        res = 0
                    resolution.setDecimals(max(-np.ceil(np.log10(res)) + 2, 1))
                    resolution.setValue(res)
            if referenceFileBlock == self:
                data = ds.read()
            else:
                if referenceFileBlock.ds is not None:
                    height = referenceFileBlock.ds.height
                    width = referenceFileBlock.ds.width
                else:
                    height = ds.height
                    width = ds.width
                data = ds.read(
                    out_shape=(ds.count, height, width), resampling=Resampling.nearest
                )

            self.data = data.squeeze()
            if self.data.ndim == 3:
                self.data = self.data.transpose(1, 2, 0)
        self.setPixmapSignal.emit()

    def loadVector(self, fn):
        # if (not osp.isfile(fn)) and (not Path(fn).root.startswith(os.sep)):
        #     return
        if not osp.isfile(fn):
            self.data = None
            self.crs = None
            return
        try:
            # import geopandas as gpd
            gdf: gpd.GeoDataFrame = gpd.read_file(fn)
        except:
            return
        gdf = gdf[~gdf.is_empty]
        self.gdf = gdf
        referenceFileBlock = ReferenceFileBlock().fileBlock
        if referenceFileBlock.ds is None:
            return
        # if (referenceFileBlock.ds.crs is not None) and \
        #     (gdf.crs is not None and gdf.crs != 4326): # bug for 4326
        #     gdf = gdf.to_crs(referenceFileBlock.ds.crs)
        #     gdf = gdf.affine_transform(
        #         (~referenceFileBlock.ds.transform).to_shapely())
        # if gdf.crs == 4326:
        #     gdf = gdf.scale(yfact=-1, origin=(0, 0))
        if (referenceFileBlock.ds.crs is not None) and (
            gdf.crs is not None
        ):  # bug for 4326
            gdf = gdf.to_crs(referenceFileBlock.ds.crs)
            gdf = gdf.affine_transform((~referenceFileBlock.ds.transform).to_shapely())
        self.ds = None
        if (self.attr is None) or (self.attr not in gdf):
            shapes = [(val, (idx % 254) + 1) for idx, val in enumerate(gdf.geometry)]
        else:
            shapes = gdf[["geometry", self.attr]].values.tolist()
        label = rasterize(
            shapes,
            out_shape=referenceFileBlock.ds.shape,
            fill=0,
            default_value=255,
            dtype=np.uint8,
        )
        self.data = self.palette[label]
        self.setPixmapSignal.emit()

    @staticmethod
    def is_raster(fn):
        if Path(fn).suffix.lower() in {".jpg", ".bmp", ".png", ".tif", ".tiff", ".jp2"}:
            return True
        else:
            return False

    @staticmethod
    def is_vector(fn):
        if Path(fn).suffix.lower() in {".shp", ".geojson"}:
            return True
        else:
            return False

    def get(self, key):
        return self.loadDataFuncs.get(key, None)

    def set(self, key, val):
        self.loadDataFuncs[key] = val

    def loadCustom(self, fn):
        data = None
        ds = None
        ref_ds = getattr(ReferenceFileBlock().fileBlock, "ds")
        if ref_ds is None:
            return
        # height = getattr(ref_ds, 'height', 0)
        # width = getattr(ref_ds, 'width', 0)
        # count = getattr(ref_ds, 'count', 0)
        crs = getattr(ref_ds, "crs", None)
        transform = getattr(ref_ds, "transform", rio.Affine.identity())
        shape = getattr(ref_ds, "shape", (0, 0))
        load = self.loadDataFuncs.get("load", None)
        if load is None:
            return
        try:
            data = load(
                obj=self,
                fn=fn,
                shape=shape,
                crs=crs,
                transform=transform,
                ref_ds=ref_ds,
            )
        except:
            return
        # palette = self.loadDataFuncs.get('palette', None)
        # if palette:
        #     data = np.asarray(palette, np.uint8)[data]
        self.data = data
        self.ds = ds
        self.setPixmapSignal.emit()

    @Slot()
    def readImage(self, *args, **kwargs):
        def fun():
            if not self.fileLineEdit.text():
                return
            path = Path(self.fileLineEdit.text())
            if not path.is_file():
                self.data = None
                return
            if self.modeComboBox.currentText() == "custom":
                self.loadCustom(path)
            else:
                if self.is_raster(path):
                    self.loadRaster(path)
                elif self.is_vector(path):
                    self.loadVector(path)

                    # if self.crs.linear_units == 'metre':
                    #     _, factor = self.crs.linear_units_factor

        thread = threading.Thread(target=fun)
        thread.start()

    def loadVectorV2(self, fn):
        # if (not osp.isfile(fn)) and (not Path(fn).root.startswith(os.sep)):
        #     return
        if not osp.isfile(fn):
            self.data = None
            self.crs = None
            return
        try:
            # import geopandas as gpd
            gdf: gpd.GeoDataFrame = gpd.read_file(fn)
        except:
            return
        gdf = gdf[~gdf.is_empty]
        self.gdf = gdf
        referenceFileBlock = ReferenceFileBlock().fileBlock
        if referenceFileBlock.ds is None:
            return
        # if (referenceFileBlock.ds.crs is not None) and \
        #     (gdf.crs is not None and gdf.crs != 4326): # bug for 4326
        #     gdf = gdf.to_crs(referenceFileBlock.ds.crs)
        #     gdf = gdf.affine_transform(
        #         (~referenceFileBlock.ds.transform).to_shapely())
        # if gdf.crs == 4326:
        #     gdf = gdf.scale(yfact=-1, origin=(0, 0))
        if (referenceFileBlock.ds.crs is not None) and (
            gdf.crs is not None
        ):  # bug for 4326
            gdf = gdf.to_crs(referenceFileBlock.ds.crs)
            gdf = gdf.affine_transform((~referenceFileBlock.ds.transform).to_shapely())
        self.ds = None
        if (self.attr is None) or (self.attr not in gdf):
            shapes = [(val, (idx % 254) + 1) for idx, val in enumerate(gdf.geometry)]
        else:
            shapes = gdf[["geometry", self.attr]].values.tolist()
        label = rasterize(
            shapes,
            out_shape=referenceFileBlock.ds.shape,
            fill=0,
            default_value=255,
            dtype=np.uint8,
        )
        self.data = self.palette[label]
        self.setPixmapSignal.emit()

    @Slot()
    def setPixmap(self, *args, **kwargs):
        if self.data is None:
            return
        mode = self.modeComboBox.currentText()
        opacity = int(self.opacityDoubleSpinBox.value() * 255 / 100)
        if mode == "fill":
            data = self.data.copy()
            if data.ndim == 2:
                data = np.dstack([data, data, data])
            H, W = data.shape[:2]
            alpha = np.zeros_like(data[..., :1]) + opacity
            # mask = np.sum(data, axis=-1) == 0
            # alpha[mask] = 255
            data = np.concatenate([data, alpha], axis=-1)
            image = QImage(data, W, H, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(image)
        elif mode == "index":
            data = self.data.copy()
            if data.ndim != 2:
                return
            palette = np.random.randint(64, 256, (256, 4), dtype=np.uint8)
            palette[..., -1] = opacity
            palette[0] = (0, 0, 0, opacity)
            palette[-1] = (255, 255, 255, opacity)
            data = palette[data]
            H, W = data.shape[:2]
            # alpha = np.zeros_like(data[..., :1]) + opacity
            # mask = np.sum(data, axis=-1) == 0
            # alpha[mask] = 255
            # data = np.concatenate([data, alpha], axis=-1)
            image = QImage(data, W, H, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(image)
        elif mode == "outline":
            data = self.data.copy().astype(np.int)
            if data.ndim == 3:
                data = (
                    np.left_shift(data[..., 0], 16)
                    + np.left_shift(data[..., 1], 8)
                    + data[..., 2]
                )
            boundary = find_boundaries(data)

            # alpha = np.zeros_like(boundary, dtype=np.uint8)
            # alpha[boundary] = opacity
            boundary = boundary.astype(np.uint8)
            H, W = boundary.shape[:2]
            palette = np.asarray([[0, 0, 0, 0], self.color.getRgb()], dtype=np.uint8)
            # data = np.dstack([boundary, boundary, boundary, alpha])
            data = palette[boundary]
            image = QImage(data, W, H, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(image)

            # canvas = QPixmap(pixmap.size())
            # canvas.fill(Qt.transparent)
            # painter = QPainter(canvas)
            # painter.setCompositionMode(QPainter.CompositionMode_Source)
            # painter.drawPixmap(0, 0, pixmap)
            # painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            # painter.fillRect(canvas.rect(), QColor(0, 0, 0, int(255*opacity)))
            # painter.end()
        elif mode == "normal":
            data = self.data.copy()
            # alpha = np.zeros_like(data[..., :1]) + opacity
            # alpha = np.empty_like(data).fil

            if data.ndim == 2:
                if data.dtype == np.uint8:
                    if data.max() == 1:
                        data = data * 255
                    H, W = data.shape
                    image = QImage(data, W, H, W, QImage.Format_Grayscale8)
            elif data.ndim == 3:
                H, W, C = data.shape
                if C == 3:
                    alpha = np.full_like(data[..., :1], opacity)
                    data = np.concatenate([data, alpha], axis=-1)
                    if data.dtype == np.int16:
                        data = data.astype(np.uint8)
                    if data.dtype == np.uint8:
                        image = QImage(data, W, H, QImage.Format_RGBA8888_Premultiplied)
                elif C == 4 and data.dtype == np.uint8:
                    image = QImage(data, W, H, QImage.Format_RGBA8888_Premultiplied)
            else:
                raise NotImplementedError
            try:
                pixmap = QPixmap.fromImage(image)
            except:
                return
        elif mode == "custom":
            data = self.data
            palette = self.loadDataFuncs.get("palette", None)
            if (data.ndim == 2) and (palette is not None):
                palette = np.asarray(palette, np.uint8)
                data = palette[data]
            data = np.ascontiguousarray(data)
            if data.ndim == 2:
                if data.dtype == np.uint8:
                    H, W = data.shape
                    image = QImage(data, W, H, W, QImage.Format_Grayscale8)
            elif data.ndim == 3:
                H, W, C = data.shape
                if C == 3:
                    alpha = np.full_like(data[..., :1], opacity)
                    data = np.concatenate([data, alpha], axis=-1)
                    if data.dtype == np.uint8:
                        image = QImage(data, W, H, QImage.Format_RGBA8888_Premultiplied)
                    elif data.dtype == np.int16:
                        image = QImage(
                            data.astype(np.uint8), W, H, QImage.Format_RGB888
                        )
                elif C == 4 and data.dtype == np.uint8:
                    image = QImage(data, W, H, QImage.Format_RGBA8888_Premultiplied)
            else:
                raise NotImplementedError
            try:
                # the image should convert to pixelmap for display in Qt
                pixmap = QPixmap.fromImage(image)
            except:
                return
        else:
            raise NotImplementedError

        self.pixmapItem.setPixmap(pixmap)
        if ReferenceFileBlock().fileBlock == self:
            Sync().syncSignal.fitInViewSignal.emit()


class FileGroupBox(QGroupBox):
    """main and only widget of the FileDialog widget, contains a group of FileBlock widgets"""

    addItemSignal = Signal(FileBlock)
    # delItemSignal = Signal()
    def __init__(self, *args, **kwargs):
        super(FileGroupBox, self).__init__(*args, **kwargs)
        self.layout = QVBoxLayout(self)
        # self.layout.setAlignment(Qt.AlignRight)

        count = QSpinBox()
        count.setMinimum(1)
        count.setSingleStep(1)
        count.setPrefix("count: ")
        count.setValue(1)
        self.countSpinBox = count
        self.countSpinBox.setAlignment(Qt.AlignCenter)
        self.countSpinBox.setMaximumWidth(200)
        self.layout.addWidget(self.countSpinBox, alignment=Qt.AlignCenter)
        self.countSpinBox.valueChanged.connect(self.modifyItems)

        # self.fileBlocks = []
        for _ in range(self.countSpinBox.value()):
            self.addItem()

    def fileBlocks(self):
        return [
            self.layout.itemAt(index).widget()
            for index in range(1, self.layout.count())
        ]

    def count(self):
        return self.layout.count()

    def itemAt(self, index):
        return self.layout.itemAt(index)

    def addItem(self):
        fileBlock = FileBlock(self)
        # self.fileBlocks.append(fileBlock)
        self.layout.addWidget(fileBlock)
        self.addItemSignal.emit(fileBlock)

    def delItem(self):
        item = self.layout.itemAt(self.count() - 1)
        widget = item.widget()
        widget.setParent(None)
        self.layout.removeWidget(widget)
        # widget.delLater()
        if widget.pixmapItem.scene():
            widget.pixmapItem.scene().removeItem(widget.pixmapItem)
        del widget
        # self.delItemSignal.emit(self.count())

    def modifyItems(self):
        if self.countSpinBox.value() > self.layout.count() - 1:
            for _ in range(self.layout.count() - 1, self.countSpinBox.value()):
                self.addItem()
        elif self.countSpinBox.value() < self.layout.count():
            for _ in range(self.countSpinBox.value(), self.layout.count() - 1):
                self.delItem()


class FileDialog(QDialog):
    """window that will be shown when double click the a view in the grid layout"""

    def __init__(self, *args, **kwargs):
        super(FileDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("File Dialog")
        self.setMinimumWidth(800)
        self.layout = QVBoxLayout(self)
        self.fileGroupBox = FileGroupBox(self)
        self.layout.addWidget(self.fileGroupBox)
        self.setModal(True)

    def setPath(self, path, index=0):
        # index = index + 1 # the first is count widget
        if index < len(self.fileGroupBox.fileBlocks()):
            fileBlock = self.fileGroupBox.fileBlocks()[index]
            fileBlock.fileLineEdit.setText(str(path))
            # item = self.fileGroupBox.layout.itemAt(index)
            # if isinstance(path, pl.WindowsPath):

            # item.widget().fileLineEdit.setText(str(path))
        # ...

    def closeEvent(self, event):
        history = History()
        for fileBlock in self.fileGroupBox.fileBlocks():
            history.addItem(fileBlock.fileLineEdit.text())
        return super(FileDialog, self).closeEvent(event)
