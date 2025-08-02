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

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication, QToolTip
from qgis.core import Qgis as QGis, QgsApplication, QgsCoordinateTransform, QgsExpression, QgsFeature, \
    QgsGeometry, QgsMapLayer, QgsPointXY, QgsProject, QgsRectangle, QgsUnitTypes, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsRubberBand, QgsAttributeEditorContext, QgsMessageBar
from qgis.utils import iface

from .geometry_shapes_dialog import GeometryShapesDialog


class GeometryTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.dlg = GeometryShapesDialog()
        self.capturing = False
        self.startPoint = None
        self.endPoint = None
        self.rubberBand = None
        self.helperBand = None
        self.canvas = canvas

        cursor = QgsApplication.getThemeCursor(QgsApplication.Cursor.CapturePoint)
        self.setCursor(cursor)

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

    def start_capturing(self):
        """Capturing has started: setup the tool by initializing the rubber band and capturing mode"""
        # apply application settings for the rubber band
        settings = QSettings()
        settings.beginGroup('qgis/digitizing')
        line_width = settings.value('line_width', 1, type=int)
        fill_color = QColor(settings.value('fill_color_red', 255, type=int),
                            settings.value('fill_color_green', 0, type=int),
                            settings.value('fill_color_blue', 0, type=int),
                            settings.value('fill_color_alpha', 31, type=int))
        line_color = QColor(settings.value('line_color_red', 255, type=int),
                            settings.value('line_color_green', 0, type=int),
                            settings.value('line_color_blue', 0, type=int),
                            settings.value('line_color_alpha', 199, type=int))

        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(line_color)
        self.rubberBand.setFillColor(fill_color)
        self.rubberBand.setWidth(line_width)
        self.helperBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.helperBand.setColor(Qt.gray)
        self.helperBand.setFillColor(QColor(0, 0, 0, 0))
        self.helperBand.setWidth(line_width)

        self.capturing = True

    def stop_capturing(self):
        """
        Capturing will stop: adjust dimensions if needed and add feature to
        to the active layer.
        """
        self.capturing = False
  
        # cache start- and endpoints as in case the tool disappears
        # before the dialog is closed, so we can still access them
        startpoint = QgsPointXY(self.startPoint.x(), self.startPoint.y())
        endpoint = QgsPointXY(self.endPoint.x(), self.endPoint.y())

        rect = self.selection_rect()

        # fixme: need to find out why this sometimes happens (when tool deactivated while dialog is open?)
        if not rect:
            self.reset()
            return

        # fixme: use QGis project 'measurement units' in stead of project crs units
        title = 'Set size ({})'.format(QgsUnitTypes.toString(self.canvas.mapUnits()))
        self.dlg.setWindowTitle(title)
        self.dlg.width.setValue(rect.width())
        self.dlg.height.setValue(rect.height())

        enable_segments = self.__class__.__name__ == 'OvalGeometryTool'
        self.dlg.label_segments.setEnabled(enable_segments)
        self.dlg.segments.setEnabled(enable_segments)

        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            # check for a valid result from the dialog
            if self.dlg.width.value() <= 0 or self.dlg.height.value() <= 0:
                iface.messageBar().pushMessage("Add feature",
                    "Invalid dimensions (must be numeric and greater than zero)",
                    level=QGis.Warning, duration=5)
                self.reset()
                return

            # retrieve cached start- and endpoint and adjust based on entered dimensions
            self.startPoint = startpoint
            self.endPoint = endpoint
            if self.startPoint.x() < self.endPoint.x():
                self.endPoint.setX(self.startPoint.x() + self.dlg.width.value())
            else:
                self.endPoint.setX(self.startPoint.x() - self.dlg.width.value())

            if self.startPoint.y() < self.endPoint.y():
                self.endPoint.setY(self.startPoint.y() + self.dlg.height.value())
            else:
                self.endPoint.setY(self.startPoint.y() - self.dlg.height.value())

            self.add_feature_to_layer()
        else:
            self.reset()

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # there must be an active polygon layer
            layer = self.canvas.currentLayer()
            if not layer or layer.type() != QgsMapLayer.VectorLayer or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
                iface.messageBar().pushInfo("Add feature", "No active polygon layer")
                return

            if not self.capturing:
                self.start_capturing()
                self.startPoint = self.toMapCoordinates(event.pos())
                self.endPoint = self.startPoint
            else:
                self.capture_position(event)
                self.stop_capturing()
        elif event.button() == Qt.RightButton:
            self.reset()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reset()

    def canvasMoveEvent(self, event):
        if self.capturing:
            self.capture_position(event)
            self.show_rubberband()

            if self.canvas.underMouse():
                rect = self.selection_rect()
                if rect is not None:
                    QToolTip.showText(self.canvas.mapToGlobal(self.canvas.mouseLastXY()),
                                      self.tooltip_text(rect),
                                      self.canvas)

    def capture_position(self, event):
        """
        Record the position of the mouse pointer and adjust if keyboard modifier is pressed

        :type event: qgis.gui.QgsMapMouseEvent
        """
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

    def show_rubberband(self):
        """
         Draw to 'rubber band' to the map canvas as a preview of the shape

         *To be implemented by child class*
         """
        pass

    def add_feature_to_layer(self):
        """Adds the just created shape to the active layer as a feature"""

        layer = self.canvas.currentLayer()
        feature = QgsFeature(layer.fields())
        feature.setGeometry(self.transformed_geometry(layer))

        # If the layer has attributes, set default attribute values and open the feature form for editing
        if layer.fields().count():
            for idx, field in enumerate(layer.fields()):
                default_value = field.defaultValueDefinition().expression() if field.defaultValueDefinition().isValid() else None
                if default_value:
                    # Evaluate the default value expression in the context of the layer
                    context = layer.createExpressionContext()
                    value = QgsExpression(default_value).evaluate(context)
                    feature.setAttribute(idx, value)
            
            ff = iface.getFeatureForm(layer, feature)
            ff.setMode(QgsAttributeEditorContext.AddFeatureMode)
            ff.accepted.connect(self.reset)
            ff.rejected.connect(self.reset)
            ff.show()
        else:
            layer.addFeature(feature)
            self.reset()

    def geometry(self, **kwargs):
        """
        Returns the actual shape as a QgsGeometry object in the project CRS

        *To be implemented by child class*

        :rtype: qgis.core.QgsGeometry
        """
        pass

    def transformed_geometry(self, layer):
        """
        Takes a layer and returns the geometry shape as a QgsGeometry object in the that layer's CRS

        :param layer: target layer for transformation
        :type layer: qgis.core.QgsMapLayer
        :return: geometry in target layer CRS
        :rtype: qgis.core.QgsGeometry
        """
        segments = self.dlg.segments.value()
        geometry = self.geometry(seg=segments)

        source_crs = QgsProject.instance().crs()
        tr = QgsCoordinateTransform(source_crs, layer.crs(), QgsProject.instance())

        if source_crs != layer.crs():
            geometry.transform(tr)

        return geometry

    def selection_rect(self):
        """
        Returns the area between start and endpoint as a QgsRectangle in MapCoordinates

        :rtype: qgis.core.QgsRectangle
        """
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
        self.reset()
        super(GeometryTool, self).deactivate()


class OvalGeometryTool(GeometryTool):
    def stop_capturing(self):
        self.dlg.label.setText("Radius (x)")
        self.dlg.label_2.setText("Radius (y)")
        super(OvalGeometryTool, self).stop_capturing()

    def show_rubberband(self):
        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return

        geom = self.geometry()
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setToGeometry(geom, None)
        self.rubberBand.show()

        self.helperBand.reset(QgsWkbTypes.PolygonGeometry)
        box = QgsGeometry.fromRect(geom.boundingBox())
        line = QgsGeometry.fromPolylineXY([self.startPoint, self.endPoint])
        self.helperBand.setToGeometry(box, None)
        self.helperBand.addGeometry(line, None)
        self.helperBand.show()

    def geometry(self, seg=50):
        coords = []
        r_x = self.selection_rect().width()
        r_y = self.selection_rect().height()
        for i in range(seg):
            angle = i * 2 * math.pi / seg
            x = r_x * math.cos(angle)
            y = r_y * math.sin(angle)
            coords.append(QgsPointXY(x, y))

        # move to correct position
        geom = QgsGeometry.fromPolygonXY([coords])
        geom.translate(self.startPoint.x(), self.startPoint.y())
        return geom

    def tooltip_text(self, rect):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            text = "Radius: " + str(round(rect.width(), 2))
        else:
            text = "Radius x/y: " + str(round(rect.width(), 2)) + " / " + str(round(rect.height(), 2))
        return text


class RectangleGeometryTool(GeometryTool):
    def show_rubberband(self):
        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return

        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setToGeometry(self.geometry(), None)
        self.rubberBand.show()

        line = QgsGeometry.fromPolylineXY([self.startPoint, self.endPoint])
        self.helperBand.reset(QgsWkbTypes.LineGeometry)
        self.helperBand.setToGeometry(line, None)
        self.helperBand.show()

    def geometry(self, **kwargs):
        return QgsGeometry.fromRect(self.selection_rect())

    def tooltip_text(self, rect):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            text = "Size: " + str(round(rect.width(), 2))
        else:
            text = "Size x/y: " + str(round(rect.width(), 2)) + " / " + str(round(rect.height(), 2))
        return text
