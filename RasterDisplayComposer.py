# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RasterDisplayComposer
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, SIGNAL, QObject, QDir
from PyQt4.QtGui import QAction, QIcon, QFileDialog
# Initialize Qt resources from file resources.py
import resources

from qgis.core import QGis, QgsMapLayerRegistry, QgsRasterLayer
import gdal
import osr
from gdalconst import GA_ReadOnly

# Import the code for the DockWidget
from RasterDisplayComposer_dockwidget import RasterDisplayComposerDockWidget
import os.path
from lxml import etree as ET

import logging
import logging.config


logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {'format' : '%(asctime)s - %(filename)s - line %(lineno)d - %(module)s:%(funcName)s - %(levelname)s - %(message)s'},
        'console': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': "/tmp/RasterDisplayComposer.log",
            'maxBytes': 1048576,
            'backupCount': 3
        }
    },
    'loggers': {
        'default': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    },
    'disable_existing_loggers': False
})
logger = logging.getLogger('default')


class RasterDisplayComposer:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RasterDisplayComposer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&RasterDisplayComposer')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'RasterDisplayComposer')
        self.toolbar.setObjectName(u'RasterDisplayComposer')

        # print "** INITIALIZING RasterDisplayComposer"

        self.pluginIsActive = False
        self.dockwidget = None

        self.loaded_raster_layers = {}
        self.dock_is_hidden = True

        self.isLoaded = False

        #self.preLoad()

    def preLoad(self):
        """
        Preload the plugin interface
        :return:
        """
        """
        :return:
        """
        logger.debug("plugin is active: {}".format(self.pluginIsActive))
        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING RasterDisplayComposer"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = RasterDisplayComposerDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.initDockWidgetSignals()
            self.loadComboBox()
            self.updateLoadedrasterLayers()
            self.dockwidget.hide()
            self.dock_is_hidden = True

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
        return QCoreApplication.translate('RasterDisplayComposer', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
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

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        logger.debug("Init GUI")
        icon_path = ':/plugins/RasterDisplayComposer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Raster Display Composer'),
            callback=self.run,
            parent=self.iface.mainWindow())
        # QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL(""), )
        QgsMapLayerRegistry.instance().layersAdded.connect(self.updateLoadedrasterLayers)
        QgsMapLayerRegistry.instance().layerWillBeRemoved.connect(self.updateLoadedrasterLayers)
        logger.debug("Init GUI ok")

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING RasterDisplayComposer"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD RasterDisplayComposer"

        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&RasterDisplayComposer'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""
        logger.debug("Run")
        logger.debug("self.isLoaded {}".format(self.isLoaded))
        logger.debug("self.dock_is_hidden {}".format(self.dock_is_hidden))
        if not self.isLoaded:
            self.preLoad()
            self.isLoaded = True

        if self.dock_is_hidden:
            self.dockwidget.show()
            self.dock_is_hidden = False
        else:
            self.dockwidget.hide()
            self.dock_is_hidden = True

    def initDockWidgetSignals(self):
        logger.debug("initDockWidgetSignals")
        self.dockwidget.pushButton_load.clicked.connect(self.loadRGBImage)
        self.dockwidget.pushButton_refresh.clicked.connect(self.updateLoadedrasterLayers)

    def updateLoadedrasterLayers(self, layers_added=[]):
        """
        Re-write the dictionnary of loaded raster layers with new layers
        :param layers_added:
        :return:
        """
        # print layers_added
        # print "self.iface.mapCanvas().layers()", self.iface.mapCanvas().layers()
        # print "legendInterface().layers()", self.iface.legendInterface().layers()
        # print "updateLoadedRasterlayers"
        if self.isLoaded:
            logger.debug("updateLoadedrasterLayers")
            self.loaded_raster_layers = {}

            try:
                # case of layer added
                load_list = self.iface.mapCanvas().layers() + layers_added
            except TypeError:
                # case of layer deleted
                load_list = self.iface.mapCanvas().layers()

            for layer in load_list:
                if layer.type() == layer.RasterLayer:
                    # print layer
                    # print layer.source()
                    # print layer.name()
                    # print layer.type()
                    self.loaded_raster_layers[layer.name()] = layer.source()
            # print self.loaded_raster_layers
            self.loadComboBox()

    def loadComboBox(self):
        """
        Fill in the combobox with name of the loaded raster layers
        :return:
        """
        logger.debug("loadComboBox")
        for combo_box in [self.dockwidget.comboBox_red, self.dockwidget.comboBox_green,
                          self.dockwidget.comboBox_blue, self.dockwidget.comboBox_alpha]:
            combo_box.clear()
            combo_box.addItems(self.loaded_raster_layers.keys())

    def loadRGBImage(self):
        """
        Get path of selected images, run gdalbuildvrt and loa the result in qgis
        :return:
        """
        logger.debug("loadRGBImage")
        layers_to_append = []
        for combo_box in [self.dockwidget.comboBox_red, self.dockwidget.comboBox_green,
                          self.dockwidget.comboBox_blue]:
            layers_to_append.append(self.loaded_raster_layers[combo_box.currentText()])
        # print layers_to_append
        if self.dockwidget.checkBox_alpha.isChecked():
            layers_to_append.append(self.loaded_raster_layers[self.dockwidget.comboBox_alpha.currentText()])

        no_data_option = ""
        no_data = "a"
        if self.dockwidget.checkBox_noData.isChecked():
            no_data = self.dockwidget.spinBox_noData.value()
            no_data_option = "-srcnodata " + str(no_data)

        # print layers_to_append

        rasterToLoad = "/tmp/RasterDisplayComposer.VRT"
        # command = ["gdalbuildvrt -separate", no_data_option, rasterToLoad] + layers_to_append
        # print " ".join(command)
        # os.system(" ".join(command))
        root_vrt = self.createVRT(layers_to_append, no_data)
        if self.dockwidget.checkBox_save.isChecked():
            rasterToLoad = self.getOutPutVRTFilename()
            if rasterToLoad:
                self.writeVRT(root_vrt, rasterToLoad)
            else:
                rasterToLoad = '\'' + ET.tostring(root_vrt) + '\''
        else:
            rasterToLoad = '\'' + ET.tostring(root_vrt) + '\''

        band_name = self.dockwidget.lineEdit_bandName.text()
        rasterLayer = QgsRasterLayer(rasterToLoad, band_name)

        QgsMapLayerRegistry.instance().addMapLayer(rasterLayer)

    def getInfoFromImage(self, image):
        """
        Get information about image with GDAL python api
        :param image:
        :return: dictionnary with information
        """
        logger.debug("getInfoFromImage")
        dicImage = {"image": image, "noData": "a"}

        dataset = gdal.Open(str(image), GA_ReadOnly)
        if dataset is not None:
            dicImage["size"] = [dataset.RasterXSize, dataset.RasterYSize]
            dicImage["numberOfBands"] = dataset.RasterCount
            dicImage["projection"] = dataset.GetProjection()
            geotransform = dataset.GetGeoTransform()
            if geotransform is not None:
                dicImage["origin"] = [geotransform[0], geotransform[3]]
                dicImage["pixelSize"] = [geotransform[1], geotransform[5]]
                # dicImage["geotransform"] = geotransform
                geoTransformListStr = [str(x) for x in geotransform]
                dicImage["geotransform"] = ", ".join(geoTransformListStr)
            spatialReference = osr.SpatialReference()
            spatialReference.ImportFromWkt(dataset.GetProjectionRef())
            dicImage["intEpsgCode"] = str(spatialReference.GetAuthorityCode("PROJCS"))
            # get info from band 1
            band = dataset.GetRasterBand(1)
            dicImage["dataType"] = gdal.GetDataTypeName(band.DataType)
            if not band.GetNoDataValue():
                dicImage["noData"] = "a"
            else:
                dicImage["noData"] = band.GetNoDataValue()

        print dicImage
        return dicImage

    def createVRT(self, listOfImages, no_data="a"):
        """
        Create the xml of the vrt to avoid file creation on disk
        :param listOfImages:
        :return:
        """
        logger.debug("createVRT")
        vrtFilename = None
        infoFromImage = self.getInfoFromImage(listOfImages[0])
        rootNode = ET.Element('VRTDataset')
        totalXSize = infoFromImage["size"][0]
        totalYSize = infoFromImage["size"][1]
        dataType = infoFromImage["dataType"]

        # for each band red green blue
        for index, image in enumerate(listOfImages):
            #  <VRTRasterBand dataType="Byte" band="1">
            bandNode = ET.SubElement(rootNode, "VRTRasterBand", {'dataType': str(dataType), 'band': str(index + 1)})

            # <NoDataValue>-100.0</NoDataValue>
            if no_data == "a":
                no_data = infoFromImage["noData"]
            if no_data != "a":
                node = ET.SubElement(bandNode, 'NoDataValue')
                node.text = str(no_data)
            # <SourceFilename relativeToVRT="1">nine_band.dat</SourceFilename>
            sourceNode = ET.SubElement(bandNode, 'SimpleSource')

            node = ET.SubElement(sourceNode, 'SourceFilename', {'relativeToVRT': '1'})
            node.text = image
            # <SourceBand>1</SourceBand>
            node = ET.SubElement(sourceNode, 'SourceBand')
            node.text = str(1)
            # <SrcRect xOff="0" yOff="0" xSize="1000" ySize="1000"/>
            node = ET.SubElement(sourceNode, 'SrcRect',
                                 {'xOff': '0', 'yOff': '0', 'xSize': str(totalXSize), 'ySize': str(totalYSize)})
            # <DstRect xOff="0" yOff="0" xSize="1000" ySize="1000"/>
            node = ET.SubElement(sourceNode, 'DstRect',
                                 {'xOff': '0', 'yOff': '0', 'xSize': str(totalXSize), 'ySize': str(totalYSize)})
            # bandNode.attrib['dataType'] = str(dataType)

        rootNode.attrib['rasterXSize'] = str(totalXSize)
        rootNode.attrib['rasterYSize'] = str(totalYSize)
        node = ET.SubElement(rootNode, 'SRS')
        node.text = "EPSG:" + str(infoFromImage["intEpsgCode"])  # projection

        geotransformNode = ET.SubElement(rootNode, 'GeoTransform')
        geotransformNode.text = infoFromImage["geotransform"]
        return rootNode

    def getOutPutVRTFilename(self):
        """
        Get name of the output VRT. The folder of the output filename will be saved in settings for next time
        :return: filename of the vrt
        """
        logger.debug("getOutPutVRTFilename")
        settings = QSettings()
        lastFolder = settings.value("rasterDisplayComposer_vrtlastFolder")

        if lastFolder:
            path = lastFolder
        else:
            path = QDir.currentPath()

        fileOpened = QFileDialog.getOpenFileName(None, "Load a raster file", path)

        settings.setValue("rasterDisplayComposer_vrtlastFolder", os.path.dirname(fileOpened))
        settings.sync()
        return fileOpened

    def writeVRT(self, vrt_xml, output_filename):
        """
        Write the given xml in the given output_filename
        :param vrt_xml:
        :param output_filename:
        :return:
        """
        logger.debug("writeVRT")
        tree = ET.ElementTree(vrt_xml)
        f = open(output_filename, "w")
        f.write(ET.tostring(tree, pretty_print=True))
        f.close()
