# -*- coding: utf-8 -*-

"""
/***************************************************************************
 FireToolbox
                                 A QGIS plugin
 A collection of fire insights related algorithms
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-08-30
        copyright            : (C) 2023 by Fernando Badilla Veliz - Fire2a.com
        email                : fbadilla@ing.uchile.cl
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

__author__ = "Fernando Badilla Veliz - Fire2a.com"
__date__ = "2023-08-30"
__copyright__ = "(C) 2023 by Fernando Badilla Veliz - Fire2a.com"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import processing
from qgis.core import (QgsFeatureSink, QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer, QgsVectorLayer)
from qgis.PyQt.QtCore import QCoreApplication


class ClusterizeAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT = "INPUT"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT,
                description=self.tr("Input raster layer to clusterize"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=False,
            )
        )
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Output vector layer")))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        raster = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        output = processing.run(
            "gdal:polygonize",
            {
                "BAND": 1,
                "EIGHT_CONNECTEDNESS": False,
                "EXTRA": "",
                "FIELD": "DN",
                "INPUT": raster,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        vector_layer = QgsVectorLayer(output["OUTPUT"], "polygonized", "ogr")

        feedback.pushInfo(
            "Clusterize algorithm finished.\n"
            f"name: {vector_layer.name()}\n"
            f"CRS: {vector_layer.crs().authid()}\n"
            f"geometry type: {vector_layer.geometryType()}\n"
            f"wkbType: {vector_layer.wkbType()}\n"
            f"feature count: {vector_layer.featureCount()}\n"
            f"fields: {vector_layer.fields()}\n"
        )
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, vector_layer.fields(), vector_layer.wkbType(), vector_layer.sourceCrs()
        )

        total = 100.0 / vector_layer.featureCount() if vector_layer.featureCount() else 0
        features = vector_layer.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "Clusterize"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "experimental"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return ClusterizeAlgorithm()
