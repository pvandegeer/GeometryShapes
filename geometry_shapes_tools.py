# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryShapes
                                 A QGIS plugin
 This plugin draws basic geometry shapes with user defined measurements
                              -------------------
        begin                : 2019-02-16
        git sha              : $Format:%H$
        copyright            : (C) 2019 by P. van de Geer
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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QGis, QgsDistanceArea, QgsMessageLog
from qgis.core import QgsPoint, QgsRectangle, QgsGeometry, QgsFeature, QgsCircularStringV2, QgsPointV2
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from geometry_shapes_dialog import GeometryShapesDialog
import math

class GeometryTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.dlg = GeometryShapesDialog()
        self.capturing = False
        self.rubberBand = None
        self.startPoint = None
        self.endPoint = None
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

    def reset(self):
        self.capturing = False

    def startCapturing(self):
        self.rubberBand = QgsRubberBand(self.canvas, True)
        # self.rubberBand.setBorderColor(QColor(255, 0, 0, 199))
        self.rubberBand.setBorderColor(QColor(255, 0, 0, 255))
        self.rubberBand.setColor(QColor(255, 0, 0, 31))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.DotLine)
        self.setCursor(Qt.CrossCursor)
        self.capturing = True

    def stopCapturing(self):
        pass

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.capturing:
                self.startCapturing()
                self.startPoint = self.toMapCoordinates(event.pos())
                self.endPoint = self.startPoint
            else:
                self.endPoint = self.toMapCoordinates(event.pos())
                self.stopCapturing()

    def canvasMoveEvent(self, event):
        if self.capturing:
            self.endPoint = self.toMapCoordinates(event.pos())
            self.show_shape(self.startPoint, self.endPoint)

    def show_shape(self, startPoint, endPoint):
        pass

    def draw_shape(self):
        layer = self.canvas.currentLayer()
        feature = QgsFeature()
        feature.setGeometry(self.shape())
        pr = layer.dataProvider()
        pr.addFeatures([feature])

    def shape(self):
        pass

    # fixme: use for cleanup?
    # def deactivate(self):
    #     super(GeometryTool, self).deactivate()


class OvalGeometryTool(GeometryTool):

    def stopCapturing(self):
        self.capturing = False
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)

        # rect = self.rectangle()
        # self.dlg.width.setValue(rect.width())
        # self.dlg.height.setValue(rect.height())
        # self.dlg.show()
        #
        # result = self.dlg.exec_()
        # if result:
        #     # values are adjusted

        self.draw_shape()
        self.canvas.refresh()

        # reset
        self.rubberBand = None
        self.startPoint = None
        self.endPoint = None

    def show_shape(self, startPoint, endPoint):
        self.rubberBand.reset(QGis.Polygon)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        geom = self.shape()
        layer = self.canvas.currentLayer()
        self.rubberBand.setToGeometry(geom, layer)
        self.rubberBand.show()

    def shape_future(self):
        circle = QgsCircularStringV2()
        point1 = QgsPointV2(self.startPoint.x(), self.startPoint.y())
        point2 = QgsPointV2(self.endPoint.x(), self.endPoint.y())
        circle.setPoints([point1, point2, point1])
        return QgsGeometry(circle)

    def shape(self):
        distance = QgsDistanceArea()
        r = distance.measureLine(self.startPoint, self.endPoint)
        # multiply radius for number of segments
        seg = int(20+math.sqrt(r))
        return QgsGeometry.fromPoint(QgsPoint(self.startPoint.x(), self.startPoint.y())).buffer(r, seg)

    def radius(self):
        pass


class RectangleGeometryTool(GeometryTool):

    def stopCapturing(self):
        self.capturing = False
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)

        rect = self.rectangle()
        self.dlg.width.setValue(rect.width())
        self.dlg.height.setValue(rect.height())
        self.dlg.show()

        result = self.dlg.exec_()
        if result:
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
            self.canvas.refresh()

        # reset
        self.rubberBand = None
        self.startPoint = None
        self.endPoint = None

    def show_shape(self, startPoint, endPoint):
        self.rubberBand.reset(QGis.Polygon)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPoint(startPoint.x(), startPoint.y())
        point2 = QgsPoint(startPoint.x(), endPoint.y())
        point3 = QgsPoint(endPoint.x(), endPoint.y())
        point4 = QgsPoint(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)  # true to update canvas
        self.rubberBand.show()

    def shape(self):
        return QgsGeometry.fromRect(self.rectangle())

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)
