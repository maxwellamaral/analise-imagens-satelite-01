import ee
import geemap

# Inicializa o Earth Engine
ee.Authenticate()
ee.Initialize(project='analise-satelite-projeto-01')

# Carrega a imagem Landsat 8
image = ee.Image('LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318')

# Calcula o NDVI
ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')

# Visualiza o NDVI
ndvi_params = {'min': 0, 'max': 1, 'palette': ['blue', 'white', 'green']}
Map = geemap.Map(center=[38.0, -122.0], zoom=8)
Map.addLayer(ndvi, ndvi_params, 'NDVI')
Map.addLayerControl()
Map.to_html('map_nvdi.html')