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
from qgis.core import QGis, QgsPoint, QgsRectangle, QgsGeometry, QgsFeature
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from geometry_shapes_dialog import GeometryShapesDialog

class RectangleGeometryTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.dlg = GeometryShapesDialog()
        self.capturing = False
        self.rubberBand = None
        self.startPoint = self.endPoint = None

        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

    def reset(self):
        self.capturing = False


    def startCapturing(self):
        # fixme: get user defined current setting
        # from qgis.PyQt.QtCore import QSettings
        # disableDialog = QSettings().value('/qgis/digitizing/disable_enter_attribute_values_dialog')
        self.rubberBand = QgsRubberBand(self.canvas, True)
        # self.rubberBand.setBorderColor(QColor(255, 0, 0, 199))
        self.rubberBand.setBorderColor(QColor(255, 0, 0, 255))
        self.rubberBand.setColor(QColor(255, 0, 0, 31))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.DotLine)
        self.setCursor(Qt.CrossCursor)
        self.capturing = True

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
            # fixme: check input
            if self.startPoint.x() < self.endPoint.x():
                self.endPoint.setX(self.startPoint.x() + self.dlg.width.value())
            else:
                self.endPoint.setX(self.startPoint.x() - self.dlg.width.value())

            if self.startPoint.y() < self.endPoint.y():
                self.endPoint.setY(self.startPoint.y() + self.dlg.height.value())
            else:
                self.endPoint.setY(self.startPoint.y() - self.dlg.height.value())

            self.draw_rectangle()
            self.canvas.refresh()

        # reset
        self.rubberBand = None
        self.startPoint = self.endPoint = None


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
            self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
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

    def draw_rectangle(self):
        geometry = QgsGeometry.fromRect(self.rectangle())
        feature = QgsFeature()
        feature.setGeometry(geometry)
        layer = self.canvas.currentLayer()
        layer.addFeature(feature)

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def deactivate(self):
        super(RectangleGeometryTool, self).deactivate()
        # self.emit(SIGNAL("deactivated()"))