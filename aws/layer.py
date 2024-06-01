import os
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

# Set up the QGIS application
QgsApplication.setPrefixPath("/usr/bin/qgis", True)
qgs = QgsApplication([], False)
qgs.initQgis()

source_crs = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
crs = QgsCoordinateReferenceSystem("EPSG:32718")   # UTM zone 18S

# Create a coordinate transformation
transform_context = QgsCoordinateTransformContext()
transform = QgsCoordinateTransform(source_crs, crs, transform_context)

point = QgsPointXY(-70.2, -33.7)  # Note: longitude first, then latitude
projected_point = transform.transform(point)

# Create a point feature
feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromPointXY(projected_point))

# Create a new layer
layer = QgsVectorLayer("Point?crs=EPSG:32718", "point_layer", "memory")
if not layer.isValid():
    print("Layer failed to load!")
    qgs.exitQgis()
    exit()

# Add a field to the layer
layer.startEditing()
layer.dataProvider().addAttributes([QgsField("id", QVariant.Int)])
layer.updateFields()

# Set the feature's attribute
feature.setAttributes([1])

# Add the feature to the layer
layer.addFeature(feature)
layer.commitChanges()

# Add the layer to the current project
QgsProject.instance().addMapLayer(layer)

# Export the layer to a GeoPackage
output_path = "/tmp/point_layer.gpkg"  # Update this path to your desired output location
options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
QgsVectorFileWriter.writeAsVectorFormatV2(layer, output_path, QgsCoordinateTransformContext(), options)

# Clean up
qgs.exitQgis()
