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
import os.path
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsMapLayer

from sys import version_info

if version_info[0] >= 3:
    from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton  # Qt5
    from qgis.core import QgsWkbTypes
    from .resources3 import *
    from .geometry_shapes_tools import RectangleGeometryTool, OvalGeometryTool
else:
    from qgis.PyQt.QtGui import QAction, QMenu, QToolButton  # Qt4
    from qgis.core import QGis
    import resources
    from geometry_shapes_tools import RectangleGeometryTool, OvalGeometryTool


class GeometryShapes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeometryShapes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geometry Shapes')
        self.toolbar = self.iface.digitizeToolBar()
        self.popupMenu = QMenu()
        self.toolButton = QToolButton()
        self.toolButtonAction = None

        # Setup map tools
        self.tool = None
        self.rectTool = None
        self.ovalTool = None

        self.iface.currentLayerChanged["QgsMapLayer*"].connect(self.toggle)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeometryShapes', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            insert_before=0,
            checkable=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param insert_before: Action before which the button should be
            added to the toolbar. Defaults to None: append to end
        :type insert_before: QAction

        :param checkable: Flag indicating whether the action should
            be made checkable.
        :type checkable: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if checkable:
            action.setCheckable(True)

        if add_to_toolbar:
            self.toolbar.insertAction(insert_before, action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/GeometryShapes/mActionCapturePolygonRectangle.svg'
        self.add_action(
            icon_path,
            text=self.tr(u'Draw rectangle geometry'),
            callback=lambda checked: self.set_tool(checked, 0),
            enabled_flag=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/GeometryShapes/mActionCapturePolygonCircle.svg'
        self.add_action(
            icon_path,
            text=self.tr(u'Draw oval geometry'),
            callback=lambda checked: self.set_tool(checked, 1),
            enabled_flag=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

        # Assemble popup button
        self.popupMenu.addAction(self.actions[0])
        self.popupMenu.addAction(self.actions[1])
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.actions[0])
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.toolbar.insertWidget(self.toolbar.actions()[4], self.toolButton)
        
        # Init button state
        self.toggle()

    # fixme: set cursor
    def set_tool(self, checked, action):
        if not checked:
            self.canvas.unsetMapTool(self.tool)
            self.tool = None
            return

        if action == 0:
            self.tool = RectangleGeometryTool(self.canvas)
        else:
            self.tool = OvalGeometryTool(self.canvas)

        self.toolButton.setDefaultAction(self.actions[action])
        self.tool.setAction(self.actions[action])
        self.canvas.setMapTool(self.tool)

    # Some code here lifted from: https://gitlab.com/lbartoletti/CADDigitize/blob/master/CADDigitize.py
    # and copyright 2016 by Loïc BARTOLETTI
    def toggle(self):
        #fixme: check elsewhere
        try:
            _polygon = QgsWkbTypes.PolygonGeometry  # QGis3
        except:
            _polygon = QGis.Polygon  # QGis2

        layer = self.canvas.currentLayer()
        # Decide whether the plugin button/menu is enabled or disabled
        if layer is None:
            self.actions[0].setEnabled(False)
            self.actions[1].setEnabled(False)
        else:
            try:
                # disconnect, will be reconnected
                layer.editingStarted.disconnect(self.toggle)
            except:
                pass
            try:
                # when it becomes active layer again
                layer.editingStopped.disconnect(self.toggle)
            except:
                pass

            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == _polygon:
                layer.editingStarted.connect(self.toggle)
                layer.editingStopped.connect(self.toggle)

            if layer.isEditable() and layer.geometryType() == _polygon:
                self.actions[0].setEnabled(True)
                self.actions[1].setEnabled(True)
            else:
                self.actions[0].setEnabled(False)
                self.actions[1].setEnabled(False)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr(u'&Geometry Shapes'), action)
            try:
                action.triggered.disconnect()
            except (TypeError, AttributeError):
                pass

        self.popupMenu.clear()
        self.toolbar.removeAction(self.toolButtonAction)

        layer = self.canvas.currentLayer()
        if layer:
            try:
                layer.editingStarted.disconnect(self.toggle)
            except (TypeError, AttributeError):
                pass
            try:
                layer.editingStopped.disconnect(self.toggle)
            except (TypeError, AttributeError):
                pass
            try:
                self.iface.currentLayerChanged["QgsMapLayer*"].disconnect(self.toggle)
            except (TypeError, AttributeError):
                pass

