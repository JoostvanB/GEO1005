# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpatialDecisionDockWidget
                                 A QGIS plugin
 This is a SDSS template for the GEO1005 course
                             -------------------
        begin                : 2015-11-02
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Jorge Gil, TU Delft
        email                : j.a.lopesgil@tudelft.nl
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

from PyQt4 import QtGui, QtCore, uic
from qgis.core import *
from PyQt4.QtCore import *
from qgis.networkanalysis import *
from qgis.gui import *
import processing

# matplotlib for the charts
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Initialize Qt resources from file resources.py
import resources

import os
import os.path
import random
import csv
import time

from . import utility_functions as uf


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'spatial_decision_dockwidget_base.ui'))


class SpatialDecisionDockWidget(QtGui.QDockWidget, FORM_CLASS, QgsMapTool):

    closingPlugin = QtCore.pyqtSignal()
    #custom signals
    updateAttribute = QtCore.pyqtSignal(str)

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(SpatialDecisionDockWidget, self).__init__(parent)

        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # define globals
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.npuntos = 0
        self.userTool = self.canvas.mapTool()
        # set up GUI operation signals
        # data
        self.openScenarioButton.clicked.connect(self.openScenario)
        self.saveScenarioButton.clicked.connect(self.saveScenario)
        self.checkBoxDemand.stateChanged.connect(lambda: self.updateLayers(self.checkBoxDemand.text(),self.checkBoxDemand.isChecked()))
        self.checkBoxIncome.stateChanged.connect(lambda: self.updateLayers(self.checkBoxIncome.text(), self.checkBoxIncome.isChecked()))
        self.checkBoxPOI.stateChanged.connect(lambda: self.updateLayers(self.checkBoxPOI.text(), self.checkBoxPOI.isChecked()))
        self.checkBoxChargingSpots.stateChanged.connect(lambda: self.updateLayers(self.checkBoxChargingSpots.text(), self.checkBoxChargingSpots.isChecked()))
        self.checkBoxRoads.stateChanged.connect(lambda: self.updateLayers(self.checkBoxRoads.text(), self.checkBoxRoads.isChecked()))
        self.checkBoxWaterways.stateChanged.connect(lambda: self.updateLayers(self.checkBoxWaterways.text(), self.checkBoxWaterways.isChecked()))
        self.checkBoxRailways.stateChanged.connect(lambda: self.updateLayers(self.checkBoxRailways.text(), self.checkBoxRailways.isChecked()))
        self.pushButtonAdd.clicked.connect(self.selectClickTool)
        self.pushButtonConfirmPoint.clicked.connect(self.enterPoi)

        # reporting
        self.emitPoint = QgsMapToolEmitPoint(self.canvas)
        self.emitPoint.canvasClicked.connect(self.getPoint)

        # initialisation
        #self.updateLayers()

        #run simple tests
#######
#   Data functions
#######

    def openScenario(self,filename=""):
        scenario_open = False
        scenario_file = os.path.join(u'QGIS files','Week 5 project 2.0.qgs')
        # check if file exists
        if os.path.isfile(scenario_file):
            self.iface.addProject(scenario_file)
            scenario_open = True
        else:
            last_dir = uf.getLastDir("SpatialDecision")
            new_file = QtGui.QFileDialog.getOpenFileName(self, "", last_dir, "(*.qgs)")
            if new_file:
                self.iface.addProject(unicode(new_file))
                scenario_open = True
        #if scenario_open:
        #    self.updateLayers()

    def saveScenario(self):
        self.iface.actionSaveProject()

    def updateLayers(self, layerText, status):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        #self.selectLayerCombo.clear()
        if layers:
            layer_names = uf.getLayersListNames(layers)
            layer = uf.getLegendLayerByName(self.iface, layerText)
            if layer:
                layerInCanvas = QgsMapCanvasLayer(layer)
                legend = self.iface.legendInterface()
                legend.setLayerVisible(layer, status)
            else:
                print("error")
        else:
            print("error")


            #self.selectLayerCombo.addItems(layer_names)
            #self.setSelectedLayer()
        #else:
            #self.selectAttributeCombo.clear()
            #self.clearChart()
    """
    def setSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        self.updateAttributes(layer)
    

    def getSelectedLayer(self):
        layer_name = self.selectLayerCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,layer_name)
        return layer
    """

    def updateAttributes(self, layer):
        self.selectAttributeCombo.clear()
        if layer:
            self.clearReport()
            self.clearChart()
            fields = uf.getFieldNames(layer)
            if fields:
                self.selectAttributeCombo.addItems(fields)
                self.setSelectedAttribute()
                # send list to the report list window
                self.updateReport(fields)


    def setSelectedAttribute(self):
        field_name = self.selectAttributeCombo.currentText()
        self.updateAttribute.emit(field_name)

    def getSelectedAttribute(self):
        field_name = self.selectAttributeCombo.currentText()
        return field_name

    def canvasReleaseEvent(self, event):
        self.lineEdit.setText("Hola")
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        # self.selectLayerCombo.clear()
        # you neet to set which layers will you identify here which is in your case is just 'parish_layer'
        listOfFeatures = []
        for i in layers:
            listOfFeatures.append(QgsMapToolIdentify(self.canvas).identify(event.x(), event.y(), [i],QgsMapToolIdentify.TopDownStopAtFirst))
        for features in listOfFeatures:
            if len(features) > 0:
            # here you get the selected feature
                feature = features[0].mFeature
            # And here you get the attribute's value
                try:
                    parishName = self.lineEdit.setText(feature["Demand"])
                except:
                    pass
        x = event.pos().x()
        y = event.pos().y()
        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

#######
#    Analysis functions
#######
    # route functions

    def getNetwork(self):
        roads_layer = self.getSelectedLayer()
        if roads_layer:
            # see if there is an obstacles layer to subtract roads from the network
            obstacles_layer = uf.getLegendLayerByName(self.iface, "Obstacles")
            if obstacles_layer:
                # retrieve roads outside obstacles (inside = False)
                features = uf.getFeaturesByIntersection(roads_layer, obstacles_layer, False)
                # add these roads to a new temporary layer
                road_network = uf.createTempLayer('Temp_Network','LINESTRING',roads_layer.crs().postgisSrid(),[],[])
                road_network.dataProvider().addFeatures(features)
            else:
                road_network = roads_layer
            return road_network
        else:
            return

    def buildNetwork(self):
        self.network_layer = self.getNetwork()
        if self.network_layer:
            # get the points to be used as origin and destination
            # in this case gets the centroid of the selected features
            selected_sources = self.getSelectedLayer().selectedFeatures()
            source_points = [feature.geometry().centroid().asPoint() for feature in selected_sources]
            # build the graph including these points
            if len(source_points) > 1:
                self.graph, self.tied_points = uf.makeUndirectedGraph(self.network_layer, source_points)
                # the tied points are the new source_points on the graph
                if self.graph and self.tied_points:
                    text = "network is built for %s points" % len(self.tied_points)
                    self.insertReport(text)
        return

    def calculateRoute(self):
        # origin and destination must be in the set of tied_points
        options = len(self.tied_points)
        if options > 1:
            # origin and destination are given as an index in the tied_points list
            origin = 0
            destination = random.randint(1,options-1)
            # calculate the shortest path for the given origin and destination
            path = uf.calculateRouteDijkstra(self.graph, self.tied_points, origin, destination)
            # store the route results in temporary layer called "Routes"
            routes_layer = uf.getLegendLayerByName(self.iface, "Routes")
            # create one if it doesn't exist
            if not routes_layer:
                attribs = ['id']
                types = [QtCore.QVariant.String]
                routes_layer = uf.createTempLayer('Routes','LINESTRING',self.network_layer.crs().postgisSrid(), attribs, types)
                uf.loadTempLayer(routes_layer)
            # insert route line
            for route in routes_layer.getFeatures():
                print route.id()
            uf.insertTempFeatures(routes_layer, [path], [['testing',100.00]])
            buffer = processing.runandload('qgis:fixeddistancebuffer',routes_layer,10.0,5,False,None)
            #self.refreshCanvas(routes_layer)

    def deleteRoutes(self):
        routes_layer = uf.getLegendLayerByName(self.iface, "Routes")
        if routes_layer:
            ids = uf.getAllFeatureIds(routes_layer)
            routes_layer.startEditing()
            for id in ids:
                routes_layer.deleteFeature(id)
            routes_layer.commitChanges()

    def getServiceAreaCutoff(self):
        cutoff = self.serviceAreaCutoffEdit.text()
        if uf.isNumeric(cutoff):
            return uf.convertNumeric(cutoff)
        else:
            return 0

    def calculateServiceArea(self):
        options = len(self.tied_points)
        if options > 0:
            # origin is given as an index in the tied_points list
            origin = random.randint(1,options-1)
            cutoff_distance = self.getServiceAreaCutoff()
            if cutoff_distance == 0:
                return
            service_area = uf.calculateServiceArea(self.graph, self.tied_points, origin, cutoff_distance)
            # store the service area results in temporary layer called "Service_Area"
            area_layer = uf.getLegendLayerByName(self.iface, "Service_Area")
            # create one if it doesn't exist
            if not area_layer:
                attribs = ['cost']
                types = [QtCore.QVariant.Double]
                area_layer = uf.createTempLayer('Service_Area','POINT',self.network_layer.crs().postgisSrid(), attribs, types)
                uf.loadTempLayer(area_layer)
                area_layer.setLayerName('Service_Area')
            # insert service area points
            geoms = []
            values = []
            for point in service_area.itervalues():
                # each point is a tuple with geometry and cost
                geoms.append(point[0])
                # in the case of values, it expects a list of multiple values in each item - list of lists
                values.append([cutoff_distance])
            uf.insertTempFeatures(area_layer, geoms, values)
            self.refreshCanvas(area_layer)

    # buffer functions
    def getBufferCutoff(self):
        cutoff = self.bufferCutoffEdit.text()
        if uf.isNumeric(cutoff):
            return uf.convertNumeric(cutoff)
        else:
            return 0

    def calculateBuffer(self):
        origins = self.getSelectedLayer().selectedFeatures()
        layer = self.getSelectedLayer()
        if origins > 0:
            cutoff_distance = self.getBufferCutoff()
            buffers = {}
            for point in origins:
                geom = point.geometry()
                buffers[point.id()] = geom.buffer(cutoff_distance,12).asPolygon()
            # store the buffer results in temporary layer called "Buffers"
            buffer_layer = uf.getLegendLayerByName(self.iface, "Buffers")
            # create one if it doesn't exist
            if not buffer_layer:
                attribs = ['id', 'distance']
                types = [QtCore.QVariant.String, QtCore.QVariant.Double]
                buffer_layer = uf.createTempLayer('Buffers','POLYGON',layer.crs().postgisSrid(), attribs, types)
                uf.loadTempLayer(buffer_layer)
                buffer_layer.setLayerName('Buffers')
            # insert buffer polygons
            geoms = []
            values = []
            for buffer in buffers.iteritems():
                # each buffer has an id and a geometry
                geoms.append(buffer[1])
                # in the case of values, it expects a list of multiple values in each item - list of lists
                values.append([buffer[0],cutoff_distance])
            uf.insertTempFeatures(buffer_layer, geoms, values)
            self.refreshCanvas(buffer_layer)

    def calculateIntersection(self):
        # use the buffer to cut from another layer
        cutter = uf.getLegendLayerByName(self.iface, "Buffers")
        # use the selected layer for cutting
        layer = self.getSelectedLayer()
        if cutter.featureCount() > 0:
            # get the intersections between the two layers
            intersection = processing.runandload('qgis:intersection',layer,cutter,None)
            intersection_layer = uf.getLegendLayerByName(self.iface, "Intersection")
            # prepare results layer
            save_path = "%s/dissolve_results.shp" % QgsProject.instance().homePath()
            # dissolve grouping by origin id
            dissolve = processing.runandload('qgis:dissolve',intersection_layer,False,'id',save_path)
            dissolved_layer = uf.getLegendLayerByName(self.iface, "Dissolved")
            dissolved_layer.setLayerName('Buffer Intersection')
            # close intersections intermediary layer
            QgsMapLayerRegistry.instance().removeMapLayers([intersection_layer.id()])

            # add an 'area' field and calculate
            # functiona can add more than one filed, therefore names and types are lists
            uf.addFields(dissolved_layer, ["area"], [QtCore.QVariant.Double])
            uf.updateField(dissolved_layer, "area","$area")

    # after adding features to layers needs a refresh (sometimes)
    def refreshCanvas(self, layer):
        if self.canvas.isCachingEnabled():
            layer.setCacheImage(None)
        else:
            self.canvas.refresh()

    # feature selection
    def selectFeaturesBuffer(self):
        layer = self.getSelectedLayer()
        buffer_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        if buffer_layer and layer:
            uf.selectFeaturesByIntersection(layer, buffer_layer, True)

    def selectFeaturesRange(self):
        layer = self.getSelectedLayer()
        # for the range takes values from the service area (max) and buffer (min) text edits
        max = self.getServiceAreaCutoff()
        min = self.getBufferCutoff()
        if layer and max and min:
            # gets list of numeric fields in layer
            fields = uf.getNumericFields(layer)
            if fields:
                # selects features with values in the range
                uf.selectFeaturesByRangeValues(layer, fields[0].name(), min, max)

    def selectFeaturesExpression(self):
        layer = self.getSelectedLayer()
        uf.selectFeaturesByExpression(layer, self.expressionEdit.text())

    def filterFeaturesExpression(self):
        layer = self.getSelectedLayer()
        uf.filterFeaturesByExpression(layer, self.expressionEdit.text())



#######
#    Reporting functions
#######
    # update a text edit field
    def updateNumberFeatures(self):
        layer = self.getSelectedLayer()
        if layer:
            count = layer.featureCount()
            self.featureCounterEdit.setText(str(count))

    # get the point when the user clicks on the canvas
    def enterPoi(self):
        # remember currently selected tool
        self.npuntos = (self.npuntos + 1)%4
        # activate coordinate capture tool
        self.canvas.setMapTool(self.userTool)
    def selectClickTool(self):
        self.canvas.setMapTool(self.emitPoint)
    def getPoint(self, mapPoint, mouseButton):
        # change tool so you don't get more than one POI
        if self.npuntos == 0:
            self.lineEditOneLat.setText(str(mapPoint.x()))
            self.lineEditOneLon.setText(str(mapPoint.y()))
        elif  self.npuntos == 1:
            self.lineEditTwoLat.setText(str(mapPoint.x()))
            self.lineEditTwoLon.setText(str(mapPoint.y()))
        elif self.npuntos == 2:
            self.lineEditThreeLat.setText(str(mapPoint.x()))
            self.lineEditThreeLon.setText(str(mapPoint.y()))
        elif self.npuntos == 3:
            self.lineEditFourLat.setText(str(mapPoint.x()))
            self.lineEditFourLon.setText(str(mapPoint.y()))



        #Get the click
        #if mapPoint:
        #    self.lineEdit.setText(mapPoint)
            # here do something with the point

