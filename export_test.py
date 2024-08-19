import ee
import geemap
import time  # Importa a função sleep
from init import GEE
import datetime

# Inicializa o GEE
gee = GEE()
ee.Initialize(gee.credentials)


# Função para aplicar fatores de escala
def apply_scale_factors(image):
    optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
    thermal_bands = image.select("ST_B.*").multiply(0.00341802).add(149.0)
    return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)


# Carrega a imagem Landsat 8
# image = ee.Image("LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318") # não funciona após inserir area de estudo
# image = ee.Image("LANDSAT/LC08/C01/T1/LC08_044034_20140318") # não funciona após inserir area de estudo
image = ee.Image("LANDSAT/LC08/C01/T1/LC08_220080_20200420") # funciona!

# Converte todas as bandas da imagem para o mesmo tipo (ex: Int16)
image = image.toInt16()

# Seleciona apenas as bandas B2, B3 e B4
# Sem os filtros, foi gerado uma imagem muito grande (512MB)
image = image.select(["B2", "B3", "B4"])

# Defina uma região de exportação com base nos limites da imagem
region = image.geometry().bounds().getInfo()["coordinates"]

study_area = ee.Geometry.Rectangle([-49.7, -28.3, -49.3, -28.7])

# Recorta a imagem para a área de estudo
image = image.clip(study_area)

# Reduz a imagem para obter os valores mínimos e máximos, utilizando maxPixels ou bestEffort
stats = image.reduceRegion(
    reducer=ee.Reducer.minMax(),
    geometry=study_area,
    scale=30,
    maxPixels=1e8,  # Aumenta o limite de pixels para 100 milhões
    bestEffort=True  # Ajusta a escala automaticamente para não exceder o limite de pixels
).getInfo()

print(f"Estatísticas da imagem (mínimo/máximo): {stats}")

# Verifique se a área tem dados válidos (máscara da imagem)
mask = image.mask().reduce(ee.Reducer.min())
mask_value = mask.reduceRegion(reducer=ee.Reducer.min(), geometry=study_area, scale=30).getInfo()
print(f"Máscara da imagem na área de estudo: {mask_value}")


# Obtém a URL da miniatura da imagem
print(image.getThumbURL({"min": 5000, "max": 23000}))

# Define a geometria da projeção da imagem
# geometry = image.geometry().getInfo()

# The line `# geometry = image.geometry().getInfo()` is a commented-out line in the code. It appears
# to be an attempt to get the geometry information of the image using the `getInfo()` method, which
# would convert the geometry object into a dictionary representation. However, since it is commented
# out, it is not being executed or used in the code.
# projection = image.select('B2').projection().getInfo()

# Condição para verificar se há dados válidos antes de continuar
if stats['B2_min'] is None or stats['B2_max'] is None:
    print("A área de estudo não contém dados válidos para a imagem selecionada.")
else:
    # Visualização da Imagem usando geemap
    m = geemap.Map()

    # Definir visualização das bandas RGB (B4, B3, B2)
    visualization_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 0.3, "gamma": 1.4}

    # Adiciona a imagem ao mapa
    m.centerObject(image, zoom=8)
    m.addLayer(image, visualization_params, "Landsat 8 - True Color")
    m.addLayerControl()  # Adiciona controles de camada ao mapa
    m.to_html("map_test.html")

    # Exporta a imagem para o Asset do GEE
    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    image_file_name = f"teste_export_{timestamp}"

    task = ee.batch.Export.image.toAsset(
        image=image,
        description=f"Teste_Export_{timestamp}",
        assetId=f"projects/analise-satelite-projeto-01/assets/{image_file_name}",
        scale=30,
        region=region,
    )

    task.start()

    # Exporta a imagem para o Google Drive
    # Não funciona
    taskGoogleDrive = ee.batch.Export.image.toDrive(
        image=image,
        description=f"Teste_Export_{timestamp}",
        folder="gee_exports",
        scale=30,
        # crs=projection['crs'],
        # crsTransform=projection['transform'],
        # fileFormat='GeoTIFF',
        # formatOptions={'cloudOptimized': True},
        region=study_area.getInfo()["coordinates"],
        maxPixels=1e13,
    )

    taskGoogleDrive.start()

    # Monitoramento da tarefa com sleep
    while taskGoogleDrive.active():
        print(f"Imagem id: {taskGoogleDrive.id}. Aguardando conclusão da exportação...")
        time.sleep(10)  # Espera 30 segundos entre verificações

    # Verifica o status final da tarefa
    status = taskGoogleDrive.status()

    if status["state"] == "COMPLETED":
        print(f"Exportação Concluída: {status}")
    else:
        print(f"Erro na exportação: {status}")

    download_url = image.getDownloadURL(
        {
            "image": image,
            "region": study_area,
            "name": f"{image_file_name}_down",
        }
    )

    print(download_url)
