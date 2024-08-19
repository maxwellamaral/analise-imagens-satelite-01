'''
Código em https://developers.google.com/earth-engine/apidocs/export-image-todrive
Não funciona
'''

import ee
# from init import GEE

# # Inicializa o GEE
# gee = GEE()
# ee.Initialize(gee.credentials)

ee.Authenticate()  # Inicia o processo de autenticação
ee.Initialize(project='analise-satelite-projeto-01')  

# A Landsat 8 surface reflectance image.
image = ee.Image(
    'LANDSAT/LC08/C02/T1_L2/LC08_044034_20210508'
).select(['SR_B.'])  # reflectance bands

# A region of interest.
region = ee.Geometry.BBox(-122.24, 37.13, -122.11, 37.20)

# Set the export "scale" and "crs" parameters.
task = ee.batch.Export.image.toDrive(
    image=image,
    description='image_export',
    folder='ee_demos2',
    region=region,
    scale=30,
    crs='EPSG:5070'
)
task.start()

# Use the "crsTransform" export parameter instead of "scale" for more control
# over the output grid. Here, "crsTransform" is set to align the output grid
# with the grid of another dataset. To view an image's CRS transform:

print(image.projection().getInfo())
task = ee.batch.Export.image.toDrive(
    image=image,
    description='image_export_crstransform',
    folder='ee_demos2',
    region=region,
    crsTransform=[30, 0, -2493045, 0, -30, 3310005],
    crs='EPSG:5070'
)
task.start()

# If the export has more than 1e8 pixels, set "maxPixels" higher.
task = ee.batch.Export.image.toDrive(
    image=image,
    description='image_export_maxpixels',
    folder='ee_demos2',
    region=region,
    scale=30,
    crs='EPSG:5070',
    maxPixels=1e13
)
task.start()

# Export a Cloud Optimized GeoTIFF (COG) by setting the "cloudOptimized"
# parameter to true.
task = ee.batch.Export.image.toDrive(
    image=image,
    description='image_export_cog',
    folder='ee_demos2',
    region=region,
    scale=30,
    crs='EPSG:5070',
    formatOptions={
        'cloudOptimized': True
    }
)
task.start()

# Define a nodata value and replace masked pixels with it using "unmask".
# Set the "sameFootprint" parameter as "false" to include pixels outside of the
# image geometry in the unmasking operation.
nodata_val = -9999
unmasked_image = image.unmask(value=nodata_val, sameFootprint=False)
# Use the "noData" key in the "formatOptions" parameter to set the nodata value
# (GeoTIFF format only).
task = ee.batch.Export.image.toDrive(
    image=unmasked_image,
    description='image_export_nodata',
    folder='ee_demos2',
    region=image.geometry(),  # full image bounds
    scale=2000,  # large scale for minimal demo
    crs='EPSG:5070',
    fileFormat='GeoTIFF',
    formatOptions={
        'noData': nodata_val
    }
)
task.start()