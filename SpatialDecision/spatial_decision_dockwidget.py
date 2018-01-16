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

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection

# Initialize Qt resources from file resources.py
import resources

import os
import os.path
import random
import numpy as np
import pandas as pd
import csv
import time

from . import utility_functions as uf
from PyQt4.QtGui import QIcon, QPixmap

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'spatial_decision_dockwidget_base.ui'))


class SpatialDecisionDockWidget(QtGui.QDockWidget, FORM_CLASS, QgsMapTool):
    # Set working directory

    closingPlugin = QtCore.pyqtSignal()
    #custom signals
    updateAttribute = QtCore.pyqtSignal(str)

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(SpatialDecisionDockWidget, self).__init__(parent)
        if os.path.isdir(os.path.join(os.path.dirname(__file__),'QGIS files')):
            os.chdir(os.path.join(os.path.dirname(__file__),'QGIS files'))
        else:
            os.mkdir(os.path.join(os.path.dirname(__file__),'QGIS files'))
            os.chdir(os.path.join(os.path.dirname(__file__), 'QGIS files'))
        self.workingDirectory = os.getcwd()
        print("The working directory is "+str(self.workingDirectory))
        self.initiated = False
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
        self.pointsID = 0
        self.userTool = QgsMapToolPan(self.canvas)

        # set up GUI operation signals
        # data

        self.loadDataButton.clicked.connect(self.loadData)
        self.saveScenariosButton.clicked.connect(self.saveScenario)
        self.checkBoxDemand.stateChanged.connect(lambda: self.updateLayers(self.checkBoxDemand.text(),self.checkBoxDemand.isChecked()))
        self.checkBoxIncome.stateChanged.connect(lambda: self.updateLayers(self.checkBoxIncome.text(), self.checkBoxIncome.isChecked()))
        self.checkBoxPOI.stateChanged.connect(lambda: self.updateLayers(self.checkBoxPOI.text(), self.checkBoxPOI.isChecked()))
        self.checkBoxChargingSpots.stateChanged.connect(lambda: self.updateLayers(self.checkBoxChargingSpots.text(), self.checkBoxChargingSpots.isChecked()))
        self.checkBoxRoads.stateChanged.connect(lambda: self.updateLayers(self.checkBoxRoads.text(), self.checkBoxRoads.isChecked()))
        self.checkBoxWaterways.stateChanged.connect(lambda: self.updateLayers(self.checkBoxWaterways.text(), self.checkBoxWaterways.isChecked()))
        self.checkBoxRailways.stateChanged.connect(lambda: self.updateLayers(self.checkBoxRailways.text(), self.checkBoxRailways.isChecked()))
        self.createScenarioButton.clicked.connect(self.createScenario)
        self.deleteScenarioButton.clicked.connect(self.deleteScenario)
        self.turnVisibilityButton.clicked.connect(self.turnVisibility)
        self.addPointsButton.clicked.connect(self.selectClickTool)
        self.confirmPointsButton.clicked.connect(self.enterPoi)
        self.deletePointsButton.clicked.connect(self.deletePoint)
        self.addAnalyzeButton.clicked.connect(self.setPointAnalysisTool)
        # analysis
        self.emitPoint = QgsMapToolEmitPoint(self.canvas)
        self.emitPoint.canvasClicked.connect(self.getPoint)
        self.pushButton.clicked.connect(self.loadPlot)
        self.deletePointTool = QgsMapToolEmitPoint(self.canvas)
        self.deletePointTool.canvasClicked.connect(self.deletePointReal)
        self.activeScenarioCombo_2.currentIndexChanged.connect(self.updateListOfScenarios)
        self.addPointAnalysisTool = QgsMapToolEmitPoint(self.canvas)
        self.addPointAnalysisTool.canvasClicked.connect(self.getPointAnalysis)
        # initialisation
        self.loadData()

        #run figure




#######
#   Overview functions
#######
    #This method loads the project which includes background data and scenarios
    def loadData(self):
        new_file = False
        scenario_file = "Week 5 project 2.0.qgs"
        print(scenario_file)
        # check if file exists
        if os.path.isfile(scenario_file):
            self.iface.addProject(scenario_file)
        else:
            last_dir = uf.getLastDir("SpatialDecision")
            new_file = QtGui.QFileDialog.getOpenFileName(self, "", last_dir, "(*.qgs)")
            if new_file:
                self.iface.addProject(unicode(new_file))

        root = QgsProject.instance().layerTreeRoot()
        found = False
        legend = self.iface.legendInterface()
        if new_file:
            self.activeScenarioCombo_2.clear()
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup):
                if child.name() == "Scenarios":
                    found = True
                    parent = child
                    if parent.children():
                        count = 0
                        for child in parent.children():
                            if not self.initiated or new_file:
                                tempLayer = uf.getLegendLayerByName(self.iface, child.name())
                                self.activeScenarioCombo_2.addItem(child.name())
                                self.activeScenarioCombo_2.setCurrentIndex(0)
                                if legend.isLayerVisible(tempLayer):
                                    self.activeScenarioCombo_2.model().item(count).setForeground(QtGui.QColor('green'))
                                    print("green")
                                else:
                                    self.activeScenarioCombo_2.model().item(count).setForeground(QtGui.QColor('red'))
                                count += 1



        if not found:
            scenarioGroup = root.insertGroup(0, "Scenarios")
        self.initiated = True

        layer = uf.getLegendLayerByName(self.iface, self.activeScenarioCombo_2.currentText())
        if layer:
            QgsVectorFileWriter.writeAsVectorFormat(layer, r'attrtable.csv', "utf-8", None, "CSV")
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            rel = pd.read_csv('attrtable.csv')
            self.tableWidget.insertRow(0)
            headers = list(rel)
            for i in headers:
                item = QtGui.QTableWidgetItem()
                item.setText(i)
                self.tableWidget.insertColumn(self.tableWidget.columnCount())
                self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

            for index, row in rel.iterrows():
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j in range(len(row)):
                    item = QtGui.QTableWidgetItem()
                    item.setText(str(row[j]))
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)


    def createScenario(self):
        nameScenario, okPressed = QtGui.QInputDialog.getText(self, "Create Scenario", "Please input the new scenario name:")
        if okPressed:

            newLayer = QgsVectorLayer("point?crs=epsg:28992", nameScenario, "memory")
            layerData = newLayer.dataProvider()
            layerData.addAttributes([QgsField("ID", QVariant.Int), QgsField("x", QVariant.Double),
                                          QgsField("y", QVariant.Double), QgsField("Demand", QVariant.Double),
                                          QgsField("Avg_Income", QVariant.Double), QgsField("Charging_a", QVariant.Double), QgsField("POI_area", QVariant.Double)])  #
            newLayer.updateFields()
            newLayer.commitChanges()
            root = QgsProject.instance().layerTreeRoot()
            parentGroup = root.findGroup("Scenarios")
            QgsMapLayerRegistry.instance().addMapLayer(newLayer, False)
            parentGroup.insertChildNode(0,QgsLayerTreeLayer(newLayer))

            self.activeScenarioCombo_2.insertItem(0, nameScenario)
            self.activeScenarioCombo_2.setCurrentIndex(0)
            legend = self.iface.legendInterface()
            if legend.isLayerVisible(newLayer):
                self.activeScenarioCombo_2.model().item(0).setForeground(QtGui.QColor('green'))
            else:
                self.activeScenarioCombo_2.model().item(0).setForeground(QtGui.QColor('red'))
            if newLayer:
                QgsVectorFileWriter.writeAsVectorFormat(newLayer, r'attrtable.csv', "utf-8", None, "CSV")
                self.tableWidget.clear()
                self.tableWidget.setRowCount(0)
                self.tableWidget.setColumnCount(0)
                rel = pd.read_csv('attrtable.csv')
                self.tableWidget.insertRow(0)
                headers = list(rel)
                for i in headers:
                    item = QtGui.QTableWidgetItem()
                    item.setText(i)
                    self.tableWidget.insertColumn(self.tableWidget.columnCount())
                    self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

                for index, row in rel.iterrows():
                    self.tableWidget.insertRow(self.tableWidget.rowCount())
                    for j in range(len(row)):
                        item = QtGui.QTableWidgetItem()
                        item.setText(str(row[j]))
                        self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)

    def deleteScenario(self):
        layerName = self.activeScenarioCombo_2.currentText()
        layerIndex = self.activeScenarioCombo_2.currentIndex()
        layer = uf.getLegendLayerByName(self.iface, layerName)
        if layer:
            QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
            self.activeScenarioCombo_2.removeItem(layerIndex)
            self.activeScenarioCombo_2.setCurrentIndex(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)
        layer = uf.getLegendLayerByName(self.iface, layerName)
        if layer:
            QgsVectorFileWriter.writeAsVectorFormat(layer, r'attrtable.csv', "utf-8", None, "CSV")
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            rel = pd.read_csv('attrtable.csv')
            self.tableWidget.insertRow(0)
            headers = list(rel)
            for i in headers:
                item = QtGui.QTableWidgetItem()
                item.setText(i)
                self.tableWidget.insertColumn(self.tableWidget.columnCount())
                self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

            for index, row in rel.iterrows():
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j in range(len(row)):
                    item = QtGui.QTableWidgetItem()
                    item.setText(str(row[j]))
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)




    def turnVisibility(self):
        index = self.activeScenarioCombo_2.currentIndex()
        text = self.activeScenarioCombo_2.currentText()
        layer = uf.getLegendLayerByName(self.iface, text)
        if layer:
            legend = self.iface.legendInterface()
            legend.setLayerVisible(layer, not legend.isLayerVisible(layer))
            if legend.isLayerVisible(layer):
                self.activeScenarioCombo_2.model().item(int(index)).setForeground(QtGui.QColor('green'))
            else:
                self.activeScenarioCombo_2.model().item(int(index)).setForeground(QtGui.QColor('red'))

    def saveScenario(self):

        self.iface.mainWindow().findChild(QtGui.QAction, 'mActionSaveProject').trigger()

    def updateLayers(self, layerText, status):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        if layers:
            layer = uf.getLegendLayerByName(self.iface, layerText)
            if layer:
                legend = self.iface.legendInterface()
                legend.setLayerVisible(layer, status)
                layerDemand = uf.getLegendLayerByName(self.iface, "Electric Vehicle Demand")
                layerIncome = uf.getLegendLayerByName(self.iface, "Average Income")
                if layerText == "Electric Vehicle Demand":
                    if self.checkBoxDemand.isChecked():
                        if self.checkBoxIncome.isChecked():
                            self.checkBoxIncome.setChecked(False)
                if layerText == "Average Income":
                    if self.checkBoxDemand.isChecked():
                        if self.checkBoxIncome.isChecked():
                            self.checkBoxDemand.setChecked(False)






    def updateListOfScenarios(self):
        layer = uf.getLegendLayerByName(self.iface, self.activeScenarioCombo_2.currentText())
        if layer:
            QgsVectorFileWriter.writeAsVectorFormat(layer, r'attrtable.csv', "utf-8", None, "CSV")
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            rel = pd.read_csv('attrtable.csv')
            self.tableWidget.insertRow(0)
            headers = list(rel)
            for i in headers:
                item = QtGui.QTableWidgetItem()
                item.setText(i)
                self.tableWidget.insertColumn(self.tableWidget.columnCount())
                self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

            for index, row in rel.iterrows():
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                for j in range(len(row)):
                    item = QtGui.QTableWidgetItem()
                    item.setText(str(row[j]))
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)

    #######
#    Analysis functions
#######

    #Plot analysis
    def plotAnalysis(self):
        def radar_factory(num_vars, frame='circle'):

            # calculate evenly-spaced axis angles
            theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
            # rotate theta such that the first axis is at the top
            theta += np.pi / 2

            def draw_poly_patch(self):
                verts = unit_poly_verts(theta)
                return plt.Polygon(verts, closed=True, edgecolor='k')

            def draw_circle_patch(self):
                # unit circle centered on (0.5, 0.5)
                return plt.Circle((0.5, 0.5), 0.5)

            patch_dict = {'polygon': draw_poly_patch, 'circle': draw_circle_patch}
            if frame not in patch_dict:
                raise ValueError('unknown value for `frame`: %s' % frame)

            class RadarAxes(PolarAxes):

                name = 'radar'
                # use 1 line segment to connect specified points
                RESOLUTION = 1
                # define draw_frame method
                draw_patch = patch_dict[frame]

                def fill(self, *args, **kwargs):
                    """Override fill so that line is closed by default"""
                    closed = kwargs.pop('closed', True)
                    return super(RadarAxes, self).fill(closed=closed, *args, **kwargs)

                def plot(self, *args, **kwargs):
                    """Override plot so that line is closed by default"""
                    lines = super(RadarAxes, self).plot(*args, **kwargs)
                    for line in lines:
                        self._close_line(line)

                def _close_line(self, line):
                    x, y = line.get_data()
                    # FIXME: markers at x[0], y[0] get doubled-up
                    if x[0] != x[-1]:
                        x = np.concatenate((x, [x[0]]))
                        y = np.concatenate((y, [y[0]]))
                        line.set_data(x, y)

                def set_varlabels(self, labels):
                    self.set_thetagrids(np.degrees(theta), labels)

                def _gen_axes_patch(self):
                    return self.draw_patch()

                def _gen_axes_spines(self):
                    if frame == 'circle':
                        return PolarAxes._gen_axes_spines(self)
                    # The following is a hack to get the spines (i.e. the axes frame)
                    # to draw correctly for a polygon frame.

                    # spine_type must be 'left', 'right', 'top', 'bottom', or `circle`.
                    spine_type = 'circle'
                    verts = unit_poly_verts(theta)
                    # close off polygon by repeating first vertex
                    verts.append(verts[0])
                    path = Path(verts)

                    spine = Spine(self, spine_type, path)
                    spine.set_transform(self.transAxes)
                    return {'polar': spine}

            register_projection(RadarAxes)
            return theta

        def unit_poly_verts(theta):
            x0, y0, r = [0.5] * 3
            verts = [(r * np.cos(t) + x0, r * np.sin(t) + y0) for t in theta]
            return verts

        def example_data():
            data = [
                ['',
                 '1',
                 '2',
                 '3',
                 '',
                 '4',
                 '5',
                 '6'],

                ('First potential spot', [
                    [0.00, 0.81, 0.96, 0.83, 0.00, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.00, 0.8, 0.9, 0.8]]),
                ('Second potential spot', [
                    [0.00, 0.41, 0.7, 0.63, 0.00, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.00, 0.5, 0.9, 0.7]]),

            ]
            return data

        if __name__ == '__main__':
            N = 8
            theta = radar_factory(N, frame='polygon')

            data = example_data()
            spoke_labels = data.pop(0)

            fig, axes = plt.subplots(figsize=(7, 7), nrows=2, ncols=1,
                                     subplot_kw=dict(projection='radar'))
            fig.subplots_adjust(wspace=0.55, hspace=0.10, top=0.85, bottom=0.05)

            colors = ['b', 'r']
            for ax, (title, case_data) in zip(axes.flatten(), data):
                ax.set_rgrids([0.2, 0.4, 0.6, 0.8], angle=90)
                ax.set_title(title, weight='bold', size='large', position=(0.5, 1))
                for d, color in zip(case_data, colors):
                    ax.plot(theta, d, color=color)
                    ax.fill(theta, d, facecolor=color, alpha=0.65)
                ax.set_varlabels(spoke_labels)

        fig.text(0.7, 0.4,
                 'Legend:\n1:Average household income \n2:Distance to closest Point of Interest \n3:Number of Points of Interest within 200m radius \n4:Average occupation of closest charging spot \n5:Demand of parking spots \n6:Distance to closest charging spot',
                 color='grey', weight='bold',
                 size='medium')

        plt.savefig('AnalysisPlot.png', bbox_inches='tight')
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
        self.canvas.setMapTool(self.userTool)
    def selectClickTool(self):
        self.canvas.setMapTool(self.emitPoint)

    def loadPlot(self):
        label = self.label
        pixmap = QPixmap('AnalysisPlot.png')
        label.setPixmap(pixmap)

    def getPoint(self, mapPoint, mouseButton):

        layer = uf.getLegendLayerByName(self.iface, self.activeScenarioCombo_2.currentText())
        self.iface.setActiveLayer(layer)
        demandLayer = uf.getLegendLayerByName(self.iface, "Electric Vehicle Demand")
        demand = 0.0
        income = 0.0
        iterations = demandLayer.getFeatures()

        for feature in iterations:
            attrs = feature.attributes()
            if (mapPoint.x() > float(attrs[1])) and (mapPoint.x() <= float(attrs[2])):
                if (mapPoint.y() > float(attrs[3])) and (mapPoint.y() <= float(attrs[4])):
                    demand = float(attrs[5])
                    income = float(attrs[6])
                    charga = float(attrs[7])
                    npoi = float(attrs[8])
        poiLayer = uf.getLegendLayerByName(self.iface, "Points Of Interest")
        iterationspoi = poiLayer.getFeatures()

        if QgsVectorDataProvider.AddFeatures:
            feat = QgsFeature(layer.pendingFields())
            for field in layer.pendingFields():
                print(field.name())
            # Or set a single attribute by key or by index:
            feat.setAttribute(0, self.pointsID)
            feat.setAttribute(1, mapPoint.x())
            feat.setAttribute(2, mapPoint.y())
            feat.setAttribute(3, demand)
            feat.setAttribute(4, income)
            feat.setAttribute(5, charga)
            feat.setAttribute(6, npoi)
            feat.setGeometry(QgsGeometry.fromPoint(mapPoint))
            (res, outFeats) = layer.dataProvider().addFeatures([feat])
        layer.updateFields()
        layer.commitChanges()
        self.canvas.refresh()
        self.pointsID += 1
        QgsVectorFileWriter.writeAsVectorFormat(layer, r'attrtable.csv', "utf-8", None, "CSV")
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)
        rel = pd.read_csv('attrtable.csv')
        self.tableWidget.insertRow(0)
        headers = list(rel)
        for i in headers:
            item = QtGui.QTableWidgetItem()
            item.setText(i)
            self.tableWidget.insertColumn(self.tableWidget.columnCount())
            self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

        for index, row in rel.iterrows():
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            for j in range(len(row)):
                item = QtGui.QTableWidgetItem()
                item.setText(str(row[j]))
                self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)

    def deletePoint(self):
        self.canvas.setMapTool(self.deletePointTool)

    def deletePointReal(self, mapPoint, mouseButton):
        layer = uf.getLegendLayerByName(self.iface, self.activeScenarioCombo_2.currentText())
        iterations = layer.getFeatures()
        for feature in iterations:
            attrs = feature.attributes()
            if (abs(mapPoint.x() - float(attrs[1])) < 50):
                if (abs(mapPoint.y() - float(attrs[2])) < 50):
                    print(feature.id())
                    layer.dataProvider().deleteFeatures([feature.id()])

        layer.commitChanges()
        self.canvas.refresh()

        QgsVectorFileWriter.writeAsVectorFormat(layer, r'attrtable.csv', "utf-8", None, "CSV")
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)
        rel = pd.read_csv('attrtable.csv')
        self.tableWidget.insertRow(0)
        headers = list(rel)
        for i in headers:
            item = QtGui.QTableWidgetItem()
            item.setText(i)
            self.tableWidget.insertColumn(self.tableWidget.columnCount())
            self.tableWidget.setItem(0, self.tableWidget.columnCount() - 1, item)

        for index, row in rel.iterrows():
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            for j in range(len(row)):
                item = QtGui.QTableWidgetItem()
                item.setText(str(row[j]))
                self.tableWidget.setItem(self.tableWidget.rowCount() - 1, j, item)

    def setPointAnalysisTool(self):
        self.canvas.setMapTool(self.deletePointTool)

