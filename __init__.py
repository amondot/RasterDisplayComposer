# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RasterDisplayComposer
                                 A QGIS plugin
 Compose RGB image display from different bands
                             -------------------
        begin                : 2016-02-13
        copyright            : (C) 2016 by Alexia Mondot
        email                : contact@mondot.fr
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
    """Load RasterDisplayComposer class from file RasterDisplayComposer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .RasterDisplayComposer import RasterDisplayComposer
    return RasterDisplayComposer(iface)
