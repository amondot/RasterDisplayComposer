# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RasterDisplayComposerDockWidget
                                 A QGIS plugin
 Compose RGB image display from different bands
                             -------------------
        begin                : 2016-02-13
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Alexia Mondot
        email                : contact@mondot.fr
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

import os

from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import pyqtSignal

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'RasterDisplayComposer_dockwidget_base.ui'))

# import loggin for debug messages
import logging
logging.basicConfig()
# create logger
logger = logging.getLogger('RasterDisplayComposer_dockWidget')
logger.setLevel(logging.INFO)


class RasterDisplayComposerDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RasterDisplayComposerDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.fileOpened = {}
        self.setupUi(self)
        self.setup_ui()

    def setup_ui(self):
        self.comboBox_alpha.hide()
        self.checkBox_alpha.hide()
        self.lineEdit_bandName.setText("RasterDisplayComposer")
        # self.comboBox_red.currentIndexChanged[str].connect(self.loadComboBox)
        # self.comboBox_green.currentIndexChanged[str].connect(self.loadComboBox)
        # self.comboBox_blue.currentIndexChanged[str].connect(self.loadComboBox)



    # def loadComboBox(self, text):
    #     sender = QtCore.QObject.sender(self)
    #     logger.info("QObject.sender() " + str(QtCore.QObject.sender(self)))
    #     if text == "Load from file...":
    #         settings = QtCore.QSettings()
    #         lastFolder = settings.value("rasterDisplayComposer_lastFolder")
    #
    #         if lastFolder:
    #             path = lastFolder
    #         else:
    #             path = QtCore.QDir.currentPath()
    #
    #         fileOpened = QtCore.QFileDialog.getOpenFileName(None, "Load a raster file", path)
    #
    #         settings.setValue("rasterDisplayComposer_lastFolder", os.path.dirname(fileOpened))
    #         settings.sync()
    #         self.fileOpened[os.path.basename(fileOpened):fileOpened]



    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

