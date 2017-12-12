# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoChargePlugin
                                 A QGIS plugin
 Plugin for cityplanner to choose best charging spot
                             -------------------
        begin                : 2017-12-12
        copyright            : (C) 2017 by J&J
        email                : joost_vb1@hotmail.com
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
    """Load GeoChargePlugin class from file GeoChargePlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geo_charge_module import GeoChargePlugin
    return GeoChargePlugin(iface)
