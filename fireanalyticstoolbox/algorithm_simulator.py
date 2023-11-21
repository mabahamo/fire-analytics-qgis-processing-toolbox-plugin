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

from datetime import datetime
from math import isclose
from multiprocessing import cpu_count
from os import chmod, kill, sep
from pathlib import Path
from platform import machine as platform_machine
from platform import system as platform_system
from shutil import copy
from signal import SIGTERM
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from typing import Any

import processing
from fire2a.raster import read_raster, transform_georef_to_coords, xy2id
from numpy import array
from osgeo import gdal
from qgis.core import (QgsMessageLog, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingContext,
                       QgsProcessingException, QgsProcessingOutputBoolean, QgsProcessingParameterBoolean,
                       QgsProcessingParameterDefinition, QgsProcessingParameterEnum, QgsProcessingParameterFile,
                       QgsProcessingParameterFolderDestination, QgsProcessingParameterGeometry,
                       QgsProcessingParameterNumber, QgsProcessingParameterRasterLayer, QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer, QgsProject, QgsRasterLayer, QgsUnitTypes)
from qgis.gui import Qgis
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .config import METRICS, SIM_OUTPUTS, STATS, TAG, jolo
from .simulator.c2fqprocess import C2F

output_args = [item["arg"] for item in SIM_OUTPUTS]
output_names = [item["name"] for item in SIM_OUTPUTS]


class FireSimulatorAlgorithm(QgsProcessingAlgorithm):
    """Cell2Fire"""

    output_dict = None
    results_dir = None
    plugin_dir = Path(__file__).parent
    c2f_path = Path(plugin_dir, "simulator", "C2F", "Cell2FireC")
    # c2f_path = Path(plugin_dir, "simulator", "C2F")
    # c2f_path = Path("/home/fdo/source/C2F-W")

    fuel_models = ["0. Scott & Burgan", "1. Kitral"]
    fuel_tables = ["spain_lookup_table.csv", "kitral_lookup_table.csv"]
    ignition_modes = [
        "0. Uniformly distributed random ignition point(s)",
        "1. Probability map distributed random ignition point(s)",
        "2. Single point on a (Vector)Layer",
    ]
    weather_modes = [
        "0. Single weather file scenario",
        "1. Random draw from multiple weathers in a directory",
        # "2. Sequential draw from multiple weathers in a directory",
    ]
    OUTPUTS = "OutputOptions"
    INSTANCE_DIR = "InstanceDirectory"
    INSTANCE_IN_PROJECT = "InstanceInProject"
    RESULTS_DIR = "ResultsDirectory"
    RESULTS_IN_INSTANCE = "ResultsInInstance"
    FUEL_MODEL = "FuelModel"
    FUEL = "FuelRaster"
    PAINTFUELS = "SetFuelLayerStyle"
    ELEVATION = "ElevationRaster"
    PV = "PvRaster"
    CBH = "CbhRaster"
    CBD = "CbdRaster"
    CCF = "CcfRaster"
    CROWN = "EnableCrownFire"
    IGNITION_MODE = "IgnitionMode"
    NSIM = "NumberOfSimulations"
    IGNIPROBMAP = "IgnitionProbabilityMap"
    IGNIPOINT = "IgnitionPointVectorLayer"
    IGNIRADIUS = "IgnitionRadius"
    WEATHER_MODE = "WeatherMode"
    WEAFILE = "WeatherFile"
    WEADIR = "WeatherDirectory"
    FMC = "FoliarMoistureContent"
    LDFMCS = "LiveAndDeadFuelMoistureContentScenario"
    SIM_THREADS = "SimulationThreads"
    RNG_SEED = "RandomNumberGeneratorSeed"
    ADD_ARGS = "OtherCliArgs"
    DRYRUN = "DryRun"
    # def validateInputCrs(self, parameters, context):
    #    """ prints friendly warning if input crs dont match across all inputs
    #    """
    #    super().validateInputCrs(parameters, context)

    def canExecute(self):
        """checks if cell2fire binary is available"""
        c2f_bin = Path(self.c2f_path, f"Cell2Fire{get_ext()}")
        if c2f_bin.is_file():
            st = c2f_bin.stat()
            chmod(c2f_bin, st.st_mode | S_IXUSR | S_IXGRP | S_IXOTH)
        else:
            return False, "Cell2Fire binary not found! Check fire2a documentation for compiling"
        #
        if platform_system() in ["Linux", "Windows"] and platform_machine() in ["x86_64", "AMD64"]:
            return True, ""
        else:
            return False, "OS {platform_system()} {platform_machine()} not supported yet"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        project_path = QgsProject().instance().absolutePath()
        # LANDSCAPE
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.FUEL_MODEL,
                description=self.tr("LANDSCAPE SECTION\nSurface fuel model"),
                options=self.fuel_models,
                allowMultiple=False,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.FUEL,
                description=self.tr("Surface fuel"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.PAINTFUELS,
                description="Style Fuel raster with selected surface fuel model (native:setlayerstyle)",
                defaultValue=True,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.ELEVATION,
                description=self.tr("Elevation"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.PV,
                description=self.tr("pv: Landscape Protection Value"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.CBH,
                description=self.tr("\ncbh: Canopy Base Height"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.CBD,
                description=self.tr("cbd: Canopy Base Density"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.CCF,
                description=self.tr("ccf: Canopy Cover Fraction"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.CROWN,
                description="Enable Crown Fire behavior",
                defaultValue=False,
                optional=False,
            )
        )
        # IGNITION
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.NSIM,
                description="\nIGNITION SECTION\nNumber of simulations",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=2,
                optional=False,
                minValue=1,
                maxValue=66642069,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.IGNITION_MODE,
                description=self.tr("Generation mode"),
                options=self.ignition_modes,
                allowMultiple=False,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.IGNIPROBMAP,
                description=self.tr("Probability map (requires generation mode 1)"),
                defaultValue=[QgsProcessing.TypeRaster],
                optional=True,
            )
        )
        self.addParameter(
            # QgsProcessingParameterGeometry(
            #     name=self.IGNIPOINT,
            #     description="Single point vector layer (requires generation mode 2)",
            #     defaultValue=None,
            #     optional=True,
            #     geometryTypes=[Qgis.GeometryType.PointGeometry],  # Qgis.GeometryType(0)],
            #     allowMultipart=False,
            QgsProcessingParameterVectorLayer(
                name=self.IGNIPOINT,
                description="Single point vector layer (requires generation mode 2)",
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.IGNIRADIUS,
                description="Radius around single point layer (requires generation mode 2)",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=0,
                optional=True,
                minValue=0,
                maxValue=11,
            )
        )
        # WEATHER
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.WEATHER_MODE,
                description=self.tr(
                    "\nWEATHER SECTION\nsource (use the weather builder algorithm if missing, must match Fuel Model)"
                ),
                options=self.weather_modes,
                allowMultiple=False,
                defaultValue=0,
            )
        )
        weafile = Path(project_path, "Weather.csv")
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.WEAFILE,
                description="Single weather file scenario (requires source 0)",
                behavior=QgsProcessingParameterFile.File,
                extension="csv",
                defaultValue=str(weafile) if weafile.is_file() else None,
                optional=True,
                fileFilter="",
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.WEADIR,
                description="From multiple weathers in a directory (requires source 1)",
                behavior=QgsProcessingParameterFile.Folder,
                extension="",
                defaultValue=None,
                optional=True,
                fileFilter="",
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.FMC,
                description="Foliar Moisture Content [40%...200%]",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=66,
                optional=False,
                minValue=40,
                maxValue=200,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.LDFMCS,
                description=(
                    "Live & Dead Fuel Moisture Content Scenario [1=dry..4=moist] (requires Scott & Burgan Fuel Model)"
                ),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=2,
                optional=True,
                minValue=1,
                maxValue=4,
            )
        )
        # RUN CONFIGURATION
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.SIM_THREADS,
                description=(
                    "\nRUN CONFIGURATION\nsimulation cpu threads (controls overall load to the computer by controlling"
                    " number of simultaneous simulations"
                    # "[check Advanced>Algorithm Settings alternative settings])"
                ),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=cpu_count() - 1,
                optional=False,
                minValue=1,
                maxValue=cpu_count(),
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.RNG_SEED,
                description="Seed for the random number generator",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=123,
                optional=False,
                minValue=1,
                maxValue=2450003,
            )
        )
        # OUTPUTS
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.OUTPUTS,
                description=self.tr(
                    "\nOUTPUTS SECTION\nOptions (TODO: separar output de procesamiento en varios algoritmos)"
                ),
                options=[item["name"] for item in SIM_OUTPUTS],
                allowMultiple=True,
                defaultValue=[0, 2, 3],
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.INSTANCE_IN_PROJECT,
                description=(
                    "Override instance directory to 'project home/firesim_yymmdd_HHMMSS' (project must be saved"
                    " locally)"
                ),
                defaultValue=False,
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name=self.INSTANCE_DIR,
                description="Instance directory (destructive action warning: empties contents if already exists)",
                defaultValue=None,
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.RESULTS_IN_INSTANCE,
                description="Override results directory to '$INSTANCE_DIR/results' (project must be saved locally)",
                defaultValue=True,
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name=self.RESULTS_DIR,
                description="Results directory (destructive action warning: empties contents if already exists)",
                defaultValue=None,
                optional=True,
                createByDefault=True,
            )
        )
        # advanced
        qpps = QgsProcessingParameterString(
            name=self.ADD_ARGS,
            description="Append additional command-line parameters (i.e., '--verbose', use with caution!)",
            optional=True,
        )
        qpps.setFlags(qpps.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(qpps)
        qppb = QgsProcessingParameterBoolean(
            name=self.DRYRUN,
            description="Don't simulate, just print the command to run",
            defaultValue=False,
            optional=True,
        )
        qppb.setFlags(qppb.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(qppb)

    def checkParameterValues(self, parameters: dict[str, Any], context: QgsProcessingContext) -> tuple[bool, str]:
        if parameters[self.IGNITION_MODE] == 1 and parameters[self.IGNIPROBMAP] is None:
            return False, f"{self.IGNIPROBMAP} cant be None if {self.IGNITION_MODE} generation is 1"
        if parameters[self.IGNITION_MODE] == 2 and parameters[self.IGNIPOINT] is None:
            return False, f"{self.IGNIPOINT} cant be None if {self.IGNITION_MODE} generation is 2"

        weafile = self.parameterAsFile(parameters, self.WEAFILE, context)
        if parameters[self.WEATHER_MODE] == 0 and weafile == "":
            return False, f"{self.WEAFILE} cant be None if {self.WEATHER_MODE} source is 0"

        weadir = self.parameterAsFile(parameters, self.WEADIR, context)
        if parameters[self.WEATHER_MODE] in [1, 2] and weadir == "":
            return False, f"{self.WEADIR} cant be None if {self.WEATHER_MODE} source is 1 or 2"

        rasters = get_rasters(self, parameters, context)
        fuels = rasters.pop("fuels")
        fuels_props = get_qgs_raster_properties(fuels)
        fuel_driver = get_gdal_driver_shortname(fuels)
        if fuel_driver != "AAIGrid":
            return False, f"fuel raster is not AAIGrid, got {fuel_driver}"
        for k, v in rasters.items():
            if v is None:
                continue
            driver = get_gdal_driver_shortname(v)
            if driver != "AAIGrid":
                return False, f'{k} is not AAIGrid, "{v.name()}" is {driver}'
            raster_props = get_qgs_raster_properties(v)
            if raster_props["units"] != QgsUnitTypes.DistanceMeters:
                unit_name = Qgis.DistanceUnit(raster_props["units"]).name
                return (
                    False,
                    f'{k} units are not meters, "{v.name()}" has "{unit_name}" units, write layer to meters-CRS!',
                )
            ok, msg = compare_raster_properties(fuels_props, raster_props)
            if not ok:
                return False, msg

        # output dirs
        project_path = QgsProject().instance().absolutePath()
        # INSTANCE DIR
        if self.parameterAsBool(parameters, self.INSTANCE_IN_PROJECT, context) and project_path != "":
            instance_dir = Path(project_path, "firesim_" + datetime.now().strftime("%y%m%d_%H%M%S"))
        else:
            instance_dir = Path(self.parameterAsString(parameters, self.INSTANCE_DIR, context))
        if next(instance_dir.glob("*"), None) is not None:
            return False, f"{instance_dir} is not empty!"
        # RESULTS DIR
        if self.parameterAsBool(parameters, self.RESULTS_IN_INSTANCE, context) and project_path != "":
            results_dir = Path(instance_dir, "results")
        else:
            results_dir = Path(self.parameterAsString(parameters, self.RESULTS_DIR, context))
        if next(results_dir.glob("*"), None) is not None:
            return False, f"{results_dir} is not empty!"

        return True, "all ok"

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # feedback.pushDebugInfo("processAlgorithm start")
        QgsMessageLog.logMessage(f"{self.name()}, in: {parameters}", tag=TAG, level=Qgis.Info)
        # feedback.pushDebugInfo(f"parameters {parameters}")
        # feedback.pushDebugInfo(f"context args: {context.asQgisProcessArguments()}")
        # GET USER INPUT
        fuel_model = self.parameterAsInt(parameters, self.FUEL_MODEL, context)
        ignition_mode = self.parameterAsInt(parameters, self.IGNITION_MODE, context)
        weather_mode = self.parameterAsInt(parameters, self.WEATHER_MODE, context)
        selected_outputs = self.parameterAsEnums(parameters, self.OUTPUTS, context)
        selected_output_strings = array(output_names)[selected_outputs]
        feedback.pushDebugInfo(
            f"fuel_model: {self.fuel_models[fuel_model]}\n"
            f"ignition_mode: {self.ignition_modes[ignition_mode]}\n"
            f"weather_mode: {self.weather_modes[weather_mode]}\n"
            f"selected_output_strings: {selected_output_strings}\n"
        )
        is_crown = self.parameterAsBool(parameters, self.CROWN, context)
        paint_fuels = self.parameterAsBool(parameters, self.PAINTFUELS, context)
        # BUILD ARGS
        # output_options = [item["name"] for item in SIM_OUTPUTS]
        args = {key: None for key in output_args}
        args["sim"] = "S" if fuel_model == 0 else "K"
        args["nsims"] = self.parameterAsInt(parameters, self.NSIM, context)
        args["seed"] = self.parameterAsInt(parameters, self.RNG_SEED, context)
        args["nthreads"] = self.parameterAsInt(parameters, self.SIM_THREADS, context)
        args["fmc"] = self.parameterAsInt(parameters, self.FMC, context)
        args["scenario"] = self.parameterAsInt(parameters, self.LDFMCS, context)
        args["cros"] = is_crown
        # match ignition_mode:
        #    case 0:
        if ignition_mode == 0:
            args["ignitions"] = False
        elif ignition_mode == 1:
            # case 1:
            args["ignitions"] = False
        elif ignition_mode == 2:
            # case 2:
            args["ignitions"] = True
            args["IgnitionRad"] = self.parameterAsInt(parameters, self.IGNIRADIUS, context)
        # match weather_mode:
        #     case 0:
        if weather_mode == 0:
            args["weather"] = "rows"
        elif weather_mode == 1:
            # case 1:
            args["weather"] = "random"
        # case 2:
        #     args["weather"] = "rows"

        # output dirs
        project_path = QgsProject().instance().absolutePath()
        # INSTANCE DIR
        if self.parameterAsBool(parameters, self.INSTANCE_IN_PROJECT, context) and project_path != "":
            instance_dir = Path(project_path, "firesim_" + datetime.now().strftime("%y%m%d_%H%M%S"))
        else:
            instance_dir = Path(self.parameterAsString(parameters, self.INSTANCE_DIR, context))
        instance_dir.mkdir(parents=True, exist_ok=True)
        feedback.pushDebugInfo(
            f"instance_dir: {str(instance_dir)}\n"
            f"_exists: {instance_dir.exists()}\n"
            f"_is_dir: {instance_dir.is_dir()}\n"
            f"_contents: {list(instance_dir.glob('*'))}\n"
        )
        # RESULTS DIR
        if self.parameterAsBool(parameters, self.RESULTS_IN_INSTANCE, context) and project_path != "":
            results_dir = Path(instance_dir, "results")
        else:
            results_dir = Path(self.parameterAsString(parameters, self.RESULTS_DIR, context))
        self.results_dir = results_dir
        results_dir.mkdir(parents=True, exist_ok=True)
        feedback.pushDebugInfo(
            f"results_dir: {str(results_dir)}\n"
            f"_exists: {results_dir.exists()}\n"
            f"_is_dir: {results_dir.is_dir()}\n"
            f"_contents: {list(results_dir.glob('*'))}\n"
        )

        # COPY
        # fuel table
        copy(Path(self.plugin_dir, "simulator", self.fuel_tables[fuel_model]), instance_dir)
        # layers
        feedback.pushDebugInfo("\n")
        raster = get_rasters(self, parameters, context)
        for k, v in raster.items():
            if v is None:
                feedback.pushDebugInfo(f"is None: {k}:{v}")
                continue
            if (
                (k in ["fuels", "elevation", "pv"])
                or (k in ["cbh", "cbd", "ccf"] and is_crown)
                or (k == "py" and ignition_mode == 1)
            ):
                feedback.pushDebugInfo(f"copy: {k}:{v}")
                if not self.parameterAsBool(parameters, self.DRYRUN, context):
                    copy(v.publicSource(), Path(instance_dir, f"{k}.asc"))
            else:
                feedback.pushDebugInfo(f"NO copy: {k}:{v}")
        feedback.pushDebugInfo("\n")

        if paint_fuels:
            feedback.pushDebugInfo(
                f"painting fuel layer: {raster['fuels'].name()}, with style {self.fuel_models[fuel_model]}"
            )
            processing.run(
                "native:setlayerstyle",
                {
                    "INPUT": raster["fuels"],
                    "STYLE": str(Path(self.plugin_dir, "simulator", f"fuel_{fuel_model}_layerStyle.qml")),
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )
            feedback.pushDebugInfo(f"painted\n")

        # IGNITION
        _, raster_props = read_raster(raster["fuels"].publicSource(), data=False)
        GT = raster_props["Transform"]
        W = raster_props["RasterXSize"]
        if ignition_mode == 2:
            point_lyr = self.parameterAsVectorLayer(parameters, self.IGNIPOINT, context)
            for feature in point_lyr.getFeatures():
                feedback.pushDebugInfo(f"feature: {feature.id()}, {feature.geometry().asWkt()}")
                point = feature.geometry().asPoint()
                x, y = point.x(), point.y()
                feedback.pushDebugInfo(f"point: {point.asWkt()}, {x}, {y}")
                i, j = transform_georef_to_coords(x, y, GT)
                feedback.pushDebugInfo(f"raster coords {i}, {j}")
                cell = xy2id(i, j, W) + 1
                feedback.pushDebugInfo(f"cell coord: {cell}")
                with open(Path(instance_dir, "Ignitions.csv"), "w") as f:
                    f.write(f"Year,Ncell\n1,{cell}")
                feedback.pushDebugInfo(f"point: {point.asWkt()}, {i}, {j}, {cell}")
            feedback.pushDebugInfo("\n")

        # WEATHER
        # TODO move checks to checkParameterValues
        if weather_mode == 0:
            weafile = self.parameterAsFile(parameters, self.WEAFILE, context)
            if weafile == "":
                # feedback.reportError("Single weather file scenario requires a file!")
                raise QgsProcessingException(self.tr("Single weather file scenario requires a file!"))
            weafileout = Path(instance_dir, "Weather.csv")
            copy(weafile, weafileout)
            feedback.pushDebugInfo(f"copy: {weafile} to {weafileout}\n")
        else:
            weadir = Path(self.parameterAsFile(parameters, self.WEADIR, context))
            weadirout = Path(instance_dir, "Weathers")
            weadirout.mkdir(parents=True, exist_ok=True)
            c = 0
            for wfile in weadir.glob("Weather[0-9]*.csv"):
                copy(wfile, weadirout)
                c += 1
            if c == 0:
                # feedback.reportError("Multiple weathers requires a directory with Weather[0-9]*.csv files!")
                raise QgsProcessingException(
                    self.tr("Multiple weathers requires a directory with Weather[0-9]*.csv files!")
                )
            feedback.pushDebugInfo(f"copy: {weadir} to {weadirout}\n{c} files copied\n")

        # BUILD COMMAND
        for opt in selected_outputs:
            args[output_args[opt]] = True
        args["input-instance-folder"] = str(instance_dir)
        args["output-folder"] = str(results_dir)
        feedback.pushDebugInfo(f"args: {args}\n")
        # cmd = "python main.py"
        cmd = "python cell2fire.py"
        for k, v in args.items():
            if v is False or v is None:
                continue
            cmd += f" --{k} {v if v is not True else ''}"
        # append cli args
        cmd += " " + self.parameterAsString(parameters, self.ADD_ARGS, context)

        if self.parameterAsBool(parameters, self.DRYRUN, context):
            feedback.pushDebugInfo(f"DRY RUN!, command:\n{cmd}\n")
            self.output_dict = {
                self.INSTANCE_DIR: str(instance_dir),
                self.RESULTS_DIR: str(results_dir),
                self.OUTPUTS: selected_outputs,
                self.DRYRUN: True,
            }
            return self.output_dict

        # RUN
        c2f = C2F(proc_dir=self.c2f_path, feedback=feedback)
        c2f.start(cmd)
        pid = c2f.pid()
        while True:
            c2f.waitForFinished(1000)
            if feedback.isCanceled():
                c2f.terminate()
                kill(pid, SIGTERM)
                feedback.pushDebugInfo("terminate signal sent")
            if c2f.ended:
                feedback.pushDebugInfo("C2F qprocess ended")
                break
            # feedback.pushDebugInfo(f"c2f loop ended:{c2f.ended}")

        self.output_dict = {
            self.INSTANCE_DIR: str(instance_dir),
            self.RESULTS_DIR: str(results_dir),
            self.OUTPUTS: selected_outputs,
        }
        feedback.pushDebugInfo(f"simulation finished, checking result log!")
        return self.output_dict

    def postProcessAlgorithm(self, context, feedback):
        # feedback.pushDebugInfo("postProcessAlgorithm start")
        output_dict = self.output_dict
        if output_dict.get(self.DRYRUN):
            feedback.pushWarning("dryrun, no postprocessing")
            return output_dict
        instance_dir = output_dict[self.INSTANCE_DIR]
        results_dir = output_dict[self.RESULTS_DIR]
        selected_outputs = output_dict[self.OUTPUTS]
        # CHECK RESULTS
        log_file = Path(results_dir, "LogFile.txt")
        if log_file.is_file() and log_file.stat().st_size > 0:
            # feedback.pushDebugInfo(log_file.read_text())
            feedback.pushInfo(f"simulator log {log_file.absolute()} ready...")
        else:
            feedback.reportError(f"log {log_file} not found or empty!")
            raise QgsProcessingException(f"{log_file} not found or empty!")
        output_dict["LogFile"] = str(log_file)
        #
        for opt in selected_outputs:
            name = output_names[opt]
            output_dict[name] = True
            feedback.pushDebugInfo(f"output: {name} True")
        #
        for st in STATS:
            files = Path(results_dir, st["dir"]).glob(st["file"] + "[0-9]*")
            if sample_file := next(files, None):
                output_dict[st["name"]] = str(sample_file)
            else:
                output_dict[st["name"]] = None

        grid = SIM_OUTPUTS[0]
        final_grid = SIM_OUTPUTS[1]
        files = Path(results_dir).glob(grid["dir"] + "[0-9]*" + sep + grid["file"] + "[0-9]*")
        if sample_file := next(files, None):
            output_dict[grid["name"]] = str(sample_file)
            output_dict[final_grid["name"]] = str(sample_file)
        else:
            output_dict[grid["name"]] = None
            output_dict[final_grid["name"]] = None

        msg = SIM_OUTPUTS[2]
        files = Path(results_dir, msg["dir"]).glob(msg["file"] + "*")
        if sample_file := next(files, None):
            output_dict[msg["name"]] = str(sample_file)
        else:
            output_dict[st["name"]] = None

        # results_dir = Path().cwd()
        # files = []
        # parent = [None]
        # for afile in results_dir.rglob("*"):
        #     if afile.is_file():
        #         new_parent = afile.parent.relative_to(results_dir)
        #         if parent[-1] != new_parent:
        #             parent += [new_parent]
        #         files += [str(afile)]
        #         print(afile.name,new_parent,len(files),len(parent))
        # output_dict["files"] = files
        with open(Path(self.results_dir, "qgis_log.html"), "w") as f:
            f.write(feedback.htmlLog())
        QgsMessageLog.logMessage(f"{self.name()}, out: {self.output_dict}", tag=TAG, level=Qgis.Info)
        return self.output_dict

    def icon(self):
        return QIcon(":/plugins/fireanalyticstoolbox/assets/forestfire.svg")

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "cell2firesimulator"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        return self.tr(self.name())
        """
        return self.tr("Cell2 Fire Simulator")

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
        return FireSimulatorAlgorithm()


def get_rasters(self, parameters, context):
    raster = dict(
        zip(
            ["fuels", "elevation", "pv", "cbh", "cbd", "ccf", "py"],
            map(
                lambda x: self.parameterAsRasterLayer(parameters, x, context),
                [
                    self.FUEL,
                    self.ELEVATION,
                    self.PV,
                    self.CBH,
                    self.CBD,
                    self.CCF,
                    self.IGNIPROBMAP,
                ],
            ),
        )
    )
    return raster


def get_gdal_driver_shortname(raster: QgsRasterLayer):
    if hasattr(raster, "publicSource"):
        raster_filename = raster.publicSource()
    else:
        raise AttributeError(f"raster {raster.name()} does not have a public source attribute!")
    filepath = Path(raster_filename)
    if not filepath.is_file() or filepath.stat().st_size == 0:
        raise FileNotFoundError(f"raster {raster.name()} file does not exist or is empty!")
    return gdal.Open(raster_filename, gdal.GA_ReadOnly).GetDriver().ShortName  # AAIGrid


def get_qgs_raster_properties(raster: QgsRasterLayer) -> dict:
    return {
        "name": raster.name(),
        "bandCount": raster.bandCount(),  # 1
        "width": raster.width(),
        "height": raster.height(),
        "crs": raster.crs().authid(),
        "units": raster.crs().mapUnits(),
        # "extent": raster.extent(),
        "xMinimum": raster.extent().xMinimum(),
        "yMinimum": raster.extent().yMinimum(),
        "xMaximum": raster.extent().xMaximum(),
        "yMaximum": raster.extent().yMaximum(),
        "rasterUnitsPerPixelX": raster.rasterUnitsPerPixelX(),
        "rasterUnitsPerPixelY": raster.rasterUnitsPerPixelY(),
    }


def compare_raster_properties(base: dict, incumbent: dict):
    for key in ["bandCount", "width", "height", "crs", "rasterUnitsPerPixelX", "rasterUnitsPerPixelY"]:
        if base[key] != incumbent[key]:
            return False, f"raster '{incumbent['name']}' {key} dont'match to fuels! {base[key]}!={incumbent[key]}"
    for key in ["xMinimum", "xMaximum"]:
        if not isclose(base[key], incumbent[key], abs_tol=base["rasterUnitsPerPixelX"]):
            return (
                False,
                (
                    f"raster '{incumbent['name']}' {key} not close enough!\n"
                    f"| {base[key]} - {incumbent[key]} | > {base['rasterUnitsPerPixelX']}"
                ),
            )
    for key in ["yMinimum", "yMaximum"]:
        if not isclose(base[key], incumbent[key], abs_tol=base["rasterUnitsPerPixelY"]):
            return (
                False,
                (
                    f"raster '{incumbent['name']}' {key} not close enough!\n"
                    f"| {base[key]} - {incumbent[key]} | > {base['rasterUnitsPerPixelY']}"
                ),
            )
    return True, "all ok"


def get_ext() -> str:
    """Get the extension for the executable file based on the platform system and machine"""
    ext = ""
    if platform_system() == "Windows":
        ext = ".exe"
    else:
        ext = f".{platform_system()}.{platform_machine()}"

    if ext not in [".exe", ".Linux.x86_64", ".Darwin.arm64", ".Darwin.x86_64"]:
        QgsMessageLog.logMessage(f"Untested platform: {ext}", tag=TAG, level=Qgis.Warning)
    if ext in [".exe", ".Darwin.arm64"]:
        QgsMessageLog.logMessage(f"Build not automated, may be using old binary: {ext}", tag=TAG, level=Qgis.Warning)

    return ext
