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

import random
from datetime import datetime
from math import isclose
from multiprocessing import cpu_count
from os import kill
from pathlib import Path
from platform import system as platform_system
from shutil import copy
from signal import SIGKILL
from time import sleep
from typing import Any

from numpy import array
from osgeo import gdal
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsProcessing,
                       QgsProcessingAlgorithm, QgsProcessingContext,
                       QgsProcessingException, QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum, QgsProcessingParameterFile,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer, QgsProject,
                       QgsRasterLayer, QgsTask)
from qgis.PyQt.QtCore import QCoreApplication

from .simulator.qgstasks import StopMeTask


class PostSimulationAlgorithm(QgsProcessingAlgorithm):
    """Cell2Fire"""

    INSTANCE_DIR = "InstanceDirectory"
    OUTPUTS = "RequestedOutputs"
    OUTPUT_FOLDER = "OutputFolder"
    plugin_dir = Path(__file__).parent
    assets_dir = Path(plugin_dir, "simulator")
    output_options = [
        "Final fire scar",
        "Propagation fire scars",
        "Propagation directed-graph",
        "Hit rate of spread",
        "Flame Length",
        "Byram Intensity",
        "Crown Fire Scar",
        "Crown Fire Fuel Consumption",
        # "Betweenness Centrality",
        # "Downstream Protection Value",
    ]

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        project_path = QgsProject().instance().absolutePath()
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INSTANCE_DIR,
                description="Cell2 Fire Simulator instance folder (normally firesim_yymmdd_HHMMSS)",
                behavior=QgsProcessingParameterFile.Folder,
                extension="",
                defaultValue=project_path if project_path != "" else None,
                optional=False,
                fileFilter="",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.OUTPUTS,
                description=self.tr("Requested Options (subset of requested for simulation)"),
                options=self.output_options,
                allowMultiple=True,
                defaultValue=list(range(len(self.output_options))),
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name=self.OUTPUT_FOLDER,
                description="Output directory",
                defaultValue=None,
                optional=True,
                createByDefault=True,
            )
        )

    def checkParameterValues(self, parameters: dict[str, Any], context: QgsProcessingContext) -> tuple[bool, str]:
        # log file exists and is not empty
        output_folder = Path(self.parameterAsString(parameters, self.INSTANCE_DIR, context))
        log_file = Path(output_folder, "results", "LogFile.txt")
        if log_file.is_file() and log_file.stat().st_size > 0:
            return True, ""
        return False, f"No results/LogFile.txt file found in instance directory ({output_folder})"

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback.pushDebugInfo("processAlgorithm start")
        feedback.pushDebugInfo(f"context args: {context.asQgisProcessArguments()}")
        # feedback.pushDebugInfo(f"parameters {parameters}")
        # GET OPTIONS
        output_options = self.parameterAsEnums(parameters, self.OUTPUTS, context)
        output_options_strings = array(self.output_options)[output_options]
        feedback.pushDebugInfo(f"output_options: {output_options_strings}\n")
        # INSTANCE FOLDER
        instance_folder = Path(self.parameterAsString(parameters, self.INSTANCE_DIR, context))
        # OUTPUT FOLDER
        output_folder = Path(self.parameterAsString(parameters, self.OUTPUT_FOLDER, context))
        # log file
        output_folder = Path(self.parameterAsString(parameters, self.INSTANCE_DIR, context))
        log_file = Path(output_folder, "results", "LogFile.txt")
        log_text = log_file.read_text()
        feedback.pushDebugInfo(log_text)

        atask = StopMeTask("A Stop Me Random", context, feedback)
        btask = StopMeTask("B Stop Me Random", context, feedback)
        task_list = []
        task_list.append(atask)
        task_list.append(btask)
        for task in task_list:
            feedback.pushDebugInfo(f"task {task.description()} {task.status()}")
            QgsApplication.taskManager().addTask(task)
            feedback.pushDebugInfo(f"task {task.description()} {task.status()}")

        c = 0
        while all([task.status() not in [QgsTask.Complete, QgsTask.Terminated] for task in task_list]):
            feedback.pushDebugInfo(f"c: {c}")
            sleep(0.5)
            if feedback.isCanceled():
                feedback.pushDebugInfo("algorithm isCanceled")
                for task in task_list:
                    if task.isActive():
                        task.cancel()
                        feedback.pushDebugInfo(f"task {task.description()} {task.status()}")
                QCoreApplication.processEvents()
            c += 1
            if c > 100:
                break
        return {self.OUTPUT_FOLDER: str(output_folder)}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "simulationresultsprocessing"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        return self.tr(self.name())
        """
        return self.tr("Simulation results processing")

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
    #     return "experimental"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return PostSimulationAlgorithm()
