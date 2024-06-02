import os
import sys
from qgis.core import (
    QgsApplication,
    QgsPointXY,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
    QgsField,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant

latitude = float(sys.argv[1]);
longitude = float(sys.argv[2]);
output_path = sys.argv[3];


# Set up the QGIS application
QgsApplication.setPrefixPath("/usr/bin/qgis", True)
qgs = QgsApplication([], False)
qgs.initQgis()

source_crs = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
crs = QgsCoordinateReferenceSystem("EPSG:32718")   # UTM zone 18S

# Create a coordinate transformation
transform_context = QgsCoordinateTransformContext()
transform = QgsCoordinateTransform(source_crs, crs, transform_context)

point = QgsPointXY(longitude, latitude)  # Note: longitude first, then latitude
projected_point = transform.transform(point)

# Create a point feature
feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromPointXY(projected_point))

# Create a new layer
layer = QgsVectorLayer("Point?crs=EPSG:32718", "ignitionPoint", "memory")

# Add the feature to the layer
layer.dataProvider().addFeature(feature)

# Update the layer's extent
layer.updateExtents()
layer.commitChanges()

# Export the layer
QgsVectorFileWriter.writeAsVectorFormat(
    layer,
    output_path,
    'UTF-8',
    layer.crs(),
    'ESRI Shapefile'
)

# Clean up
qgs.exitQgis()
