# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryShapes
                                 A QGIS plugin
 This plugin draws basic geometry shapes with user defined measurements
                             -------------------
        begin                : 2019-02-16
        copyright            : (C) 2019 by P. van de Geer
        email                : pvandegeer@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeometryShapes class from file GeometryShapes.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .geometry_shapes import GeometryShapes
    return GeometryShapes(iface)
