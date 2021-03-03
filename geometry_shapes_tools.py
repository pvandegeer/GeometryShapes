# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryShapes
                                 A QGIS plugin
 This plugin draws basic geometry shapes with user defined measurements
                              -------------------
        begin                : 2020-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2021 by P. van de Geer
                               (C) 2019 PyQGis Developer Cookbook
        email                : pvandegeer@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import math
from sys import version_info

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRectangle, QgsGeometry, QgsFeature, QgsMessageLog, QgsProject, QgsCoordinateTransform, \
    QgsUnitTypes
from qgis.gui import QgsMapTool, QgsRubberBand, QgsAttributeEditorContext
from qgis.utils import iface

if version_info[0] >= 3:
    from qgis.PyQt.QtWidgets import QApplication, QToolTip
    from qgis.core import QgsWkbTypes, QgsPointXY
    from .geometry_shapes_dialog import GeometryShapesDialog

    _polygon = QgsWkbTypes.PolygonGeometry
    _line = QgsWkbTypes.LineGeometry
else:
    from qgis.PyQt.QtGui import QApplication, QToolTip
    from qgis.core import QGis, QgsPoint as QgsPointXY
    from geometry_shapes_dialog import GeometryShapesDialog

    _polygon = QGis.Polygon
    _line = QGis.Line


class GeometryTool(QgsMapTool):
    def __init__(self, canvas):
        self.dlg = GeometryShapesDialog()
        self.capturing = False
        self.startPoint = None
        self.endPoint = None
        self.rubberBand = None
        self.helperBand = None
        self.canvas = canvas
        QgsMapTool.__init__(self, self.canvas)

    def flags(self):
        return QgsMapTool.EditTool

    def isEditTool(self):
        return True

    def reset(self):
        self.capturing = False
        self.startPoint = None
        self.endPoint = None
        if self.rubberBand is not None:
            self.canvas.scene().removeItem(self.rubberBand)
        if self.helperBand is not None:
            self.canvas.scene().removeItem(self.helperBand)
        self.rubberBand = None
        self.helperBand = None
        self.canvas.refresh()

    def startCapturing(self):
        # Fixme: use system settings
        self.rubberBand = QgsRubberBand(self.canvas, _polygon)
        self.rubberBand.setColor(QColor(255, 0, 0, 199))
        self.rubberBand.setFillColor(QColor(255, 0, 0, 31))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.DotLine)

        self.helperBand = QgsRubberBand(self.canvas, _polygon)
        self.helperBand.setColor(Qt.gray)
        self.helperBand.setFillColor(QColor(0, 0, 0, 0))
        self.helperBand.setWidth(1)
        self.helperBand.setLineStyle(Qt.DotLine)

        self.setCursor(Qt.CrossCursor)
        self.capturing = True

    def stopCapturing(self):
        self.capturing = False
        rect = self.selection_rect()

        # fixme: need to find out why this sometimes happens
        if not rect:
            self.reset()
            return

        title = 'Set size ({})'.format(QgsUnitTypes.toString(self.canvas.mapUnits()))
        self.dlg.setWindowTitle(title)
        self.dlg.width.setValue(rect.width())
        self.dlg.height.setValue(rect.height())
        self.dlg.show()

        result = self.dlg.exec_()
        if result:
            # fixme: can be NULL
            # values are adjusted
            if self.startPoint.x() < self.endPoint.x():
                self.endPoint.setX(self.startPoint.x() + self.dlg.width.value())
            else:
                self.endPoint.setX(self.startPoint.x() - self.dlg.width.value())

            if self.startPoint.y() < self.endPoint.y():
                self.endPoint.setY(self.startPoint.y() + self.dlg.height.value())
            else:
                self.endPoint.setY(self.startPoint.y() - self.dlg.height.value())

            self.draw_shape()
        else:
            self.reset()

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.capturing:
                self.startCapturing()
                self.startPoint = self.toMapCoordinates(event.pos())
                self.endPoint = self.startPoint
            else:
                self.capture_position(event)
                self.stopCapturing()
        elif event.button() == Qt.RightButton:
            self.reset()

    def canvasMoveEvent(self, event):
        if self.capturing:
            self.capture_position(event)
            self.show_shape()

            if self.canvas.underMouse():
                rect = self.selection_rect()
                if rect is not None:
                    QToolTip.showText(self.canvas.mapToGlobal(self.canvas.mouseLastXY()),
                                      self.tooltip_text(rect),
                                      self.canvas)

    def capture_position(self, event):
        # adjust dimension on the fly if Shift is pressed
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            end_point = QgsPointXY(self.toMapCoordinates(event.pos()))
            rect = QgsRectangle(self.startPoint, end_point)

            # return if start and endpoint are the same
            if rect.width() + rect.height() == 0:
                self.endPoint = self.toMapCoordinates(event.pos())
                return

            if rect.width() > rect.height():
                # make height (y) same as width in the correct direction
                if self.startPoint.y() < end_point.y():
                    end_point.setY(self.startPoint.y() + rect.width())
                else:
                    end_point.setY(self.startPoint.y() - rect.width())
            else:
                # make width (x) same as height in the correct direction
                if self.startPoint.x() < end_point.x():
                    end_point.setX(self.startPoint.x() + rect.height())
                else:
                    end_point.setX(self.startPoint.x() - rect.height())

            self.endPoint = end_point
        else:
            self.endPoint = self.toMapCoordinates(event.pos())

    def show_shape(self):
        pass

    def draw_shape(self):
        # fixme: possible to not have an active layer when it is deselected in the process
        # fail gracefully and report to user as QGis does.
        # info level: Object toevoegen: geen actieve vectorlaag.
        layer = self.canvas.currentLayer()
        feature = QgsFeature(layer.fields())
        feature.setGeometry(self.geometry(layer))

        if layer.fields().count():
            ff = iface.getFeatureForm(layer, feature)
            if version_info[0] >= 3:
                ff.setMode(QgsAttributeEditorContext.AddFeatureMode)
            ff.accepted.connect(self.reset)
            ff.rejected.connect(self.reset)
            ff.show()
        else:
            layer.addFeature(feature)
            self.reset()

    def shape(self):
        pass

    def geometry(self, layer):
        shape = self.shape()

        if version_info[0] >= 3:
            sourceCrs = QgsProject.instance().crs()
            tr = QgsCoordinateTransform(sourceCrs, layer.crs(), QgsProject.instance())
        else:
            sourceCrs = self.canvas.mapSettings().destinationCrs() if hasattr(self.canvas,
                                                                              "mapSettings") else self.canvas.mapRenderer().destinationCrs()
            tr = QgsCoordinateTransform(sourceCrs, layer.crs())

        if sourceCrs != layer.crs():
            shape.transform(tr)

        return shape

    def selection_rect(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def tooltip_text(self, rect):
        pass

    def activate(self):
        self.statusBar = iface.mainWindow().statusBar()
        self.statusBar.showMessage("Hold SHIFT to lock the ratio for perfect squares and circles")
        super(GeometryTool, self).activate()

    # fixme: use for further cleanup?
    def deactivate(self):
        self.statusBar.clearMessage()
        super(GeometryTool, self).deactivate()


class OvalGeometryTool(GeometryTool):
    def stopCapturing(self):
        self.dlg.label.setText("Radius (x)")
        self.dlg.label_2.setText("Radius (y)")
        super(OvalGeometryTool, self).stopCapturing()

    def show_shape(self):
        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return

        layer = self.canvas.currentLayer()
        geom = self.geometry(layer)

        self.rubberBand.reset(_polygon)
        self.rubberBand.setToGeometry(geom, layer)
        self.rubberBand.show()

        self.helperBand.reset(_polygon)
        box = QgsGeometry.fromRect(geom.boundingBox())
        if version_info[0] >= 3:
            line = QgsGeometry.fromPolylineXY([self.startPoint, self.endPoint])
        else:
            line = QgsGeometry.fromPolyline([self.startPoint, self.endPoint])
        self.helperBand.setToGeometry(box, layer)
        self.helperBand.addGeometry(line, layer)
        self.helperBand.show()

    def shape(self):
        seg = 50
        coords = []
        r_x = self.selection_rect().width()
        r_y = self.selection_rect().height()
        for i in range(seg):
            angle = i * 2 * math.pi / seg
            x = r_x * math.cos(angle)
            y = r_y * math.sin(angle)
            coords.append(QgsPointXY(x, y))

        # move to correct position
        if version_info[0] >= 3:
            geom = QgsGeometry.fromPolygonXY([coords])
        else:
            geom = QgsGeometry.fromPolygon([coords])
        geom.translate(self.startPoint.x(), self.startPoint.y())
        return geom

    def tooltip_text(self, rect):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            text = "Radius: " + str(round(rect.width(), 2))
        else:
            text = "Radius x/y: " + str(round(rect.width(), 2)) + " / " + str(round(rect.height(), 2))
        return text


class RectangleGeometryTool(GeometryTool):
    def show_shape(self):
        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return

        layer = self.canvas.currentLayer()

        self.rubberBand.reset(_polygon)
        self.rubberBand.setToGeometry(self.geometry(layer), layer)
        self.rubberBand.show()
        self.helperBand.reset(_line)

        if version_info[0] >= 3:
            line = QgsGeometry.fromPolylineXY([self.startPoint, self.endPoint])
        else:
            line = QgsGeometry.fromPolyline([self.startPoint, self.endPoint])

        self.helperBand.setToGeometry(line, layer)
        self.helperBand.show()

    def shape(self):
        return QgsGeometry.fromRect(self.selection_rect())

    def tooltip_text(self, rect):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            text = "Size: " + str(round(rect.width(), 2))
        else:
            text = "Size x/y: " + str(round(rect.width(), 2)) + " / " + str(round(rect.height(), 2))
        return text
