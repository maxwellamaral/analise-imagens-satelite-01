'''
Fonte: https://2engenheiros.com/2020/08/25/como-baixar-imagens-de-satelite-com-google-earth-engine-usando-python/
Funcionou
'''

import ee
import time

from init import GEE

# Inicializa o GEE
gee = GEE()
ee.Initialize(gee.credentials)

area_estudo = ee.Geometry.Rectangle([-49.7, -28.3, -49.3, -28.7])
img_landsat = ee.Image('LANDSAT/LC08/C01/T1/LC08_220080_20200420')\
    .select(['B2','B3','B4']).clip(area_estudo)
    
print(img_landsat.reduceRegion(reducer = ee.Reducer.minMax()).getInfo())
print(img_landsat.getThumbURL({'min':5000, 'max': 23000}))


task = ee.batch.Export.image.toDrive(**{
    'image': img_landsat,
    'description': 'img_B2E',
    'folder': 'EE_Output',
    'scale': 30,
    'region': area_estudo.getInfo()['coordinates']
    })
task.start()

while task.active():
    print('Salvando a imagem (id: {}).'.format(task.id))
    time.sleep(5)

download_url = img_landsat.getDownloadURL({
    'image': img_landsat,
    'region': area_estudo,
    'name': 'img_B2E_down',
})
 
print(download_url)