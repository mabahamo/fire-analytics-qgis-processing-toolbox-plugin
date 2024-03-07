# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProcessingPluginClass
                                 A QGIS plugin
 Description of the p p
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-07-12
        copyright            : (C) 2023 by fdo
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

__author__ = "fdo"
__date__ = "2023-07-12"
__copyright__ = "(C) 2023 by fdo"

# This will get replaced with a git SHA1 when you do a git archive

__version__ = "$Format:%H$"

from os import sep
from pathlib import Path
from time import sleep

import numpy as np
import pandas as pd
import processing
from pandas import DataFrame
from qgis.core import (Qgis, QgsApplication, QgsFeatureSink, QgsMessageLog, QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingException, QgsProcessingLayerPostProcessorInterface, QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterField, QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination, QgsProcessingParameterMatrix,
                       QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterRasterLayer, QgsProject, QgsTask)
from qgis.PyQt.QtCore import QCoreApplication


class SandboxAlgorithm(QgsProcessingAlgorithm):
    """comment uncomment to try"""

    # OUTPUT = "OUTPUT"
    # INPUT = "INPUT"
    # INPUT_bool = "INPUT_bool"
    INPUT_file = "INPUT_file"
    # INPUT_folder = "INPUT_folder"
    # INPUT_integer = "INPUT_integer"
    # INPUT_double = "INPUT_double"
    # INPUT_enum = "INPUT_enum"
    # IN_FIELD = "IN_FIELD"
    # IN_LAYER = "IN_LAYER"
    # OUTPUT_csv = "OUTPUT_csv"
    # o_raster = "OutputRaster"
    # o_rasterb = "OutputRasterB"
    defaultValue = None
    df = None

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # qplppi = QPLPPI()
        # add parameter
        # self.addParameter(
        #     )
        # )
        # self.addParameter(
        #     QgsProcessingParameterField(
        #         name=self.IN_FIELD,
        #         description="QgsProcessingParameterField",
        #         defaultValue="VALUE",
        #         parentLayerParameterName=self.IN_LAYER,
        #         # type: Qgis.ProcessingFieldParameterDataType = Qgis.ProcessingFieldParameterDataType.Any,
        #         allowMultiple=False,
        #         optional=False,
        #         defaultToAllFields=False,
        #     )
        # )
        # self.addParameter(
        #     QgsProcessingParameterRasterDestination(
        #         self.o_raster,
        #         self.tr(self.o_raster),
        #     )
        # )
        # devuelve in memory memory:Output layer
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         name=self.o_rasterb,
        #         description=self.tr(self.o_rasterb),
        #         type=QgsProcessing.TypeRaster,
        #         # defaultValue: Any = None,
        #         optional=True,  #: bool = False,
        #         # createByDefault: bool = True,
        #         # supportsAppend: bool = False
        #     )
        # )
        # devuelve obj con fields?
        # self.addParameter(
        #    QgsProcessingParameterFeatureSink(
        #        self.OUTPUT_csv, self.tr("CSV Output"), QgsProcessing.TypeFile
        #    )
        # )

        # We add the input vector features source. It can have any kind of geometry.
        # BUT RASTER IS NOT A GEOEMTRY
        # self.addParameter(
        #     QgsProcessingParameterFeatureSource(
        #         self.IN_LAYER,
        #         self.tr("Input TypeVectorAnyGeometry"),
        #         [QgsProcessing.TypeVectorAnyGeometry],
        #     )
        # )
        # self.addParameter(
        #     QgsProcessingParameterRasterLayer(
        #         name=self.INPUT,
        #         description=self.tr("Input Raster"),
        #         defaultValue=[QgsProcessing.TypeRaster],
        #         optional=False,
        #     )
        # )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        # self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Output layer")))

        # MATRIX
        # self.addParameter(
        #     QgsProcessingParameterMatrix(
        #         name="wea",
        #         description="weather builder",
        #         numberRows=3,
        #         hasFixedNumberRows=False,
        #         headers=["datetime", "WS", "WD", "TMP", "RH"],
        #         defaultValue=None,
        #         optional=False,
        #     )
        # )
        raise QgsProcessingException(f"error {self.defaultValue=}")
        df = pd.read_csv(Path(self.defaultValue))
        nr, nc = df.shape
        columns = df.columns
        values = df.values
        self.addParameter(
            QgsProcessingParameterMatrix(
                name="wea",
                description="weather builder",
                numberRows=nr,
                hasFixedNumberRows=False,
                headers=columns,
                defaultValue=values,
                optional=False,
            )
        )

        # bool
        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name=self.INPUT_bool,
        #         description=self.tr("Input Boolean"),
        #         defaultValue=False,
        #         optional=False,
        #     )
        # )

        # NUMBERS

        # integer
        # self.addParameter(
        #     QgsProcessingParameterNumber(
        #         name=self.INPUT_integer,
        #         description=self.tr("Input Integer"),
        #         type=QgsProcessingParameterNumber.Integer,
        #         # defaultValue = 0,
        #         optional=False,
        #         minValue=-7,
        #         maxValue=13,
        #     )
        # )

        # double
        # qppn = QgsProcessingParameterNumber(
        #     name=self.INPUT_double,
        #     description=self.tr("Input Double"),
        #     type=QgsProcessingParameterNumber.Double,
        #     defaultValue=0.69,
        #     optional=True,
        #     minValue=-1.2345,
        #     maxValue=420.666,
        # )
        # qppn.setMetadata({"widget_wrapper": {"decimals": 3}})
        # self.addParameter(qppn)

        # file
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INPUT_file,
                description=self.tr("Input File"),
                behavior=QgsProcessingParameterFile.File,
                extension="csv",  # only 1
                # >1 ?? fileFilter="csv(*.csv), text(*.txt)",
                optional=True,
                defaultValue=self.defaultValue,
                # fileFilter: str = ''
            )
        )

        # folder
        # self.addParameter(
        #     QgsProcessingParameterFile(
        #         name=self.INPUT_folder,
        #         description=self.tr("Input Folder"),
        #         behavior=QgsProcessingParameterFile.Folder,
        #         optional=True,
        #     )
        # )

        # enum
        # qppe = QgsProcessingParameterEnum(
        #     name=self.INPUT_enum,
        #     description=self.tr("Input Enum"),
        #     options=["a", "b", "c"],
        #     allowMultiple=True,
        #     defaultValue="b",
        #     optional=False,
        #     usesStaticStrings=True,
        # )
        #  qppe.param.setMetadata( {'widget_wrapper':
        #    { 'icons': [QIcon('integer.svg'), QIcon('string.svg')] }
        #  })
        # self.addParameter(qppe)

        # defaultValue = QgsProject().instance().absolutePath()
        # defaultValue = defaultValue + sep + "statistics.csv" if defaultValue != "" else None
        # qparamfd = QgsProcessingParameterFileDestination(
        #     name=self.OUTPUT_csv,
        #     description=self.tr("CSV statistics file output (overwrites!)"),
        #     fileFilter="CSV files (*.csv)",
        #     defaultValue=defaultValue,
        #     # createByDefault: bool = True,
        # )
        # qparamfd.setMetadata({"widget_wrapper": {"dontconfirmoverwrite": True}})
        # self.addParameter(qparamfd)

    def canExecute(self):
        """checks stuff before, returns True|False,fail reason"""
        if qpiap := QgsProject().instance().absolutePath():
            self.defaultValue = qpiap + sep + "treatments.csv"
        return True, "ok"

    def processAlgorithm(self, parameters, context, feedback):
        """
        feedback : <class 'qgis._core.QgsProcessingFeedback'>
        context : <class 'qgis._core.QgsProcessingContext'>
        parameters : <class 'dict'>
        """
        # feedback.pushVersionInfo()
        # feedback.pushCommandInfo("pushCommandInfo")
        # feedback.pushConsoleInfo("pushConsoleInfo")  # monospace gray
        # feedback.pushDebugInfo("pushDebugInfo")  # gray
        # feedback.pushInfo("pushInfo")
        # feedback.pushWarning("pushWarning")  # yellow
        # feedback.reportError("reportError")  # red

        # feedback.pushCommandInfo(f"{feedback=}")
        # feedback.pushCommandInfo(f"{parameters=}")
        # feedback.pushCommandInfo(f"{context.asQgisProcessArguments()=}")
        # feedback.pushCommandInfo(f"{processing.core.ProcessingConfig.cpu_count()=}")
        # feedback.pushCommandInfo(f"{context.maximumThreads()=}")
        # feedback.pushCommandInfo(f"{context.logLevel()=}")
        # feedback.pushCommandInfo(f"context env: {dir(context)}")

        # feedback.setProgress 0.0 -> 100.0
        # for i in range(6):
        #    sleep(0.1)
        #    feedback.setProgress(i*10)
        #    feedback.setProgressText(f"setProgressText {i*10}")
        #    if feedback.isCanceled():
        #        break

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        # source = self.parameterAsSource(parameters, self.INPUT, context)
        # (sink, dest_id) = self.parameterAsSink(
        #    parameters,
        #    self.OUTPUT,
        #    context,
        #    source.fields(),
        #    source.wkbType(),
        #    source.sourceCrs(),
        # )

        # input_boolean = self.parameterAsBool(parameters, self.INPUT_bool, context)
        # feedback.pushCommandInfo(f"input_boolean {input_boolean}")

        # Compute the number of steps to display within the progress bar and
        # get features from source
        # total = 100.0 / source.featureCount() if source.featureCount() else 0
        # features = source.getFeatures()
        # feedback.pushCommandInfo(f"source featureCount: {source.featureCount()}")

        # for current, feature in enumerate(features):
        #     # Stop the algorithm if cancel button has been clicked
        #     if feedback.isCanceled():
        #         break
        #     # Add a feature in the sink
        #     sink.addFeature(feature, QgsFeatureSink.FastInsert)
        #     # Update the progress bar
        #     feedback.setProgress(int(current * total))
        #     # wait
        #     sleep(0.1)

        # TODO test:
        # context.addLayerToLoadOnCompletion()
        # .addLayerToLoadOnCompletion(self, layer: str, details: QgsProcessingContext.LayerDetails)
        #       QgsProcessingContext.LayerDetails(name: str, project: QgsProject, outputName: str = '', layerTypeHint: QgsProcessingUtils.LayerHint = QgsProcessingUtils.LayerHint.UnknownType)
        # .setLayersToLoadOnCompletion()
        # .willLoadLayerOnCompletion()
        # .layerToLoadOnCompletionDetails()

        # output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_csv, context)
        # feedback.pushCommandInfo(f"output_file: {output_file}, type: {type(output_file)}")
        # df = DataFrame(np.random.randint(0, 10, (4, 3)), columns=["a", "b", "c"])
        # df.to_csv(output_file, index=False)
        # return {self.OUTPUT: dest_id, self.OUTPUT_csv: output_file}

        # i_raster = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        # feedback.pushCommandInfo(f"i_raster: {i_raster}, type: {type(i_raster)}")

        # raster_fs, raster_str = self.parameterAsSink(
        #     parameters,
        #     self.o_raster,
        #     context,
        #     # fields: QgsFields,
        #     # geometryType: Qgis.WkbType = Qgis.WkbType.NoGeometry,
        #     crs=i_raster.sourceCrs(),
        #     # sinkFlags: Union[QgsFeatureSink.SinkFlags, QgsFeatureSink.SinkFlag] = QgsFeatureSink.SinkFlags(),
        #     # createOptions: Dict[str, Any] = {},
        #     # datasourceOptions: Iterable[str] = [],
        #     # layerOptions: Iterable[str] = []
        # )
        # feedback.pushCommandInfo(f"raster_fs: {raster_fs}, type: {type(raster_fs)}")

        # raster = self.parameterAsOutputLayer(parameters, self.o_raster, context)
        # raster = self.parameterAsRasterLayer(parameters, self.o_raster, context)
        # raster = self.parameterAsSink(parameters, self.o_raster, context)
        # feedback.pushCommandInfo(f"raster: {raster}, type: {type(raster)}")

        # rasterb = self.parameterAsOutputLayer(parameters, self.o_rasterb, context)
        # rasterb = self.parameterAsRasterLayer(parameters, self.o_rasterb, context)
        # rasterb = self.parameterAsSink(parameters, self.o_rasterb, context)
        # feedback.pushCommandInfo(f"rasterb: {rasterb}, type: {type(rasterb)}")

        # rasterc = parameters[self.o_raster]
        # feedback.pushCommandInfo(f"rasterc: {rasterc}, type: {type(rasterc)}")

        # rasterd = parameters[self.o_rasterb]
        # feedback.pushCommandInfo(f"rasterd: {rasterd}, type: {type(rasterd)}")

        return {"foo": "bar"}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "templateprocessingalgorithm"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        return self.tr(self.name())
        """
        return self.tr("AASandbox")

    # def group(self):
    #     """
    #     Returns the name of the group this algorithm belongs to. This string
    #     should be localised.
    #     """
    #     return self.tr(self.groupId())

    # def groupId(self):
    #     """
    #     Returns the unique ID of the group this algorithm belongs to. This
    #     string should be fixed for the algorithm, and must not be localised.
    #     The group id should be unique within each provider. Group id should
    #     contain lowercase alphanumeric characters only and no spaces or other
    #     formatting characters.
    #     """
    #     return "zexperimental"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return SandboxAlgorithm()

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("This is an example algorithm that takes a vector layer and creates a new identical one.")

    def helpString(self):
        """
        Returns a localised help string for the algorithm. This string should
        provide more detailed help and usage information for the algorithm.
        """
        return self.tr(
            """This is an example algorithm that takes a vector layer and creates a new identical one.
        It is meant to be used as an example of how to create your own algorithms and explain methods and variables used to do it. An algorithm like this will be available in all elements, and there is not need for additional work.
        All Processing algorithms should extend the QgsProcessingAlgorithm class."""
        )

    def helpUrl(self):
        """
        Returns the URL of a web page where help for the algorithm can be found.
        """
        return "https://qgis.org"


class QPLPPI(QgsProcessingLayerPostProcessorInterface):
    """https://qgis.org/pyqgis/3.28/core/QgsProcessingLayerPostProcessorInterface.html"""

    def __init__(self):
        super().__init__()

    def postProcessLayer(self, layer, context, feedback):
        # def postProcessLayer(self, layer: QgsMapLayer, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        pass


task_status = {
    QgsTask.Queued: "Task is queued and has not begun.",  # 0
    QgsTask.OnHold: "Task is queued but on hold and will not be started.",  # 1
    QgsTask.Running: "Task is currently running.",  # 2
    QgsTask.Complete: "Task successfully completed.",  # 3
    QgsTask.Terminated: "Task was terminated or errored.",  # 4
}
