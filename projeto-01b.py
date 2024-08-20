import ee
import geemap
import time
import math
import datetime

# Função para calcular o NDVI
def calculate_ndvi(image, nir_band, red_band):
    return image.normalizedDifference([nir_band, red_band]).rename('NDVI')

# Função para aplicar máscara de nuvens ao Sentinel-2
def mask_s2_clouds(image):
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = (
        qa.bitwiseAnd(cloud_bit_mask).eq(0)
        .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    )
    return image.updateMask(mask).divide(10000)

# Função para criar mapa
def create_map(dataset, visualization, center_coords, zoom_level, map_name):
    m = geemap.Map()
    m.set_center(*center_coords, zoom_level)
    m.addLayer(dataset, visualization, map_name)
    return m

# Função para calcular a escala com base na área (Redução para 20 Mp)
def calculate_scale(area_m2, max_pixels=2e7):
    return math.sqrt(area_m2 / max_pixels)

def monitor_tasks(tasks):
    """Verifica o status das tarefas até que sejam concluídas."""
    while any([task.active() for task in tasks]):
        print("Aguardando conclusão das tarefas...")
        time.sleep(30)  # Verifica o status a cada 30 segundos
        for task in tasks:
            status = task.status()
            print(f"Tarefa {task.id}: {status['state']}")
    print("Todas as tarefas foram concluídas!")

def main():
    try:
        # Define o período de tempo
        DATE_START_LANGSAT = DATE_START_SENTINEL = '2017-01-01'
        DATE_END_LANGSAT = DATE_END_SENTINEL = '2024-01-01'

        # Ponto central da Caatinga
        CENTRAL_POINTS = [-39.5, -8.5]

        # Porcentagem máxima de cobertura de nuvens
        CLOUDY_PIXEL_PERCENTAGE = 20

        # Inicializa o GEE
        ee.Authenticate()
        ee.Initialize(project='analise-satelite-projeto-01')

        # Definir uma área de interesse (Caatinga)
        caatinga = ee.FeatureCollection('projects/ee-maxwellamaral-proj01/assets/MAPBIOMAS/caatinga')

        # Calcula a área da região de interesse em metros quadrados
        area_m2 = caatinga.geometry().area().getInfo()

        # Gerar o timestamp para nomeação dos arquivos
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        # Calcula a escala com base no limite de pixels
        scale = calculate_scale(area_m2)
        print(f"Área da região: {area_m2} metros quadrados. Escala calculada: {scale} metros.")

        # Pasta no Google Drive
        folder_drive = 'analise-satelite-projeto-01'

        # Lista de tarefas para monitoramento
        tasks = []

        # -------------------------------------------
        # Landsat 8 - Cálculo do NDVI
        # -------------------------------------------
        
        # Coleção Landsat 8
        datasetLangSat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterDate(DATE_START_LANGSAT, DATE_END_LANGSAT) \
            .filterBounds(caatinga) \
            .filter(ee.Filter.lt('CLOUD_COVER', CLOUDY_PIXEL_PERCENTAGE)) \
            .select(['SR_B5', 'SR_B4'])  # Seleciona apenas as bandas NIR e Red

        # Calcula o NDVI para Landsat 8
        ndvi_landsat = datasetLangSat.map(lambda img: calculate_ndvi(img, 'SR_B5', 'SR_B4'))

        # Conta o número de imagens filtradas
        landsat_count = datasetLangSat.size().getInfo()
        print(f"Número de imagens Landsat 8 filtradas: {landsat_count}")

        if landsat_count > 0:
            # Visualização do NDVI Landsat 8
            visualization_ndvi_landsat = {
                'min': -1,
                'max': 1,
                'palette': ['blue', 'white', 'green']
            }

            # Cria o mapa Landsat NDVI e salva como HTML
            map_landsat = create_map(ndvi_landsat.median(), visualization_ndvi_landsat, CENTRAL_POINTS, 6, "NDVI Landsat 8")
            map_landsat.to_html('map_ndvi_landsat.html')

            # Salvar NDVI Landsat no Google Drive
            landsat_image = ndvi_landsat.median().clip(caatinga)
            landsat_task = ee.batch.Export.image.toDrive(
                image=landsat_image,
                description=f'Landsat_NDVI_Export_{timestamp}',
                folder=folder_drive,
                scale=scale,
                region=caatinga.geometry().bounds().getInfo()['coordinates'],
                fileFormat='GeoTIFF'
            )
            landsat_task.start()
            tasks.append(landsat_task)
        else:
            print("Nenhuma imagem Landsat 8 disponível para o intervalo de tempo especificado.")

        # -------------------------------------------
        # Sentinel-2 - Cálculo do NDVI
        # -------------------------------------------

        # Coleção Sentinel-2
        datasetSentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterDate(DATE_START_SENTINEL, DATE_END_SENTINEL) \
            .filterBounds(caatinga) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUDY_PIXEL_PERCENTAGE)) \
            .select(['B8', 'B4'])  # Seleciona apenas as bandas NIR e Red
        
        # Calcula o NDVI para Sentinel-2
        ndvi_sentinel2 = datasetSentinel2.map(lambda img: calculate_ndvi(img, 'B8', 'B4'))

        # Conta o número de imagens filtradas
        sentinel_count = datasetSentinel2.size().getInfo()
        print(f"Número de imagens Sentinel-2 filtradas: {sentinel_count}")

        if sentinel_count > 0:
            # Visualização do NDVI Sentinel-2
            visualization_ndvi_sentinel2 = {
                'min': -1,
                'max': 1,
                'palette': ['blue', 'white', 'green']
            }

            # Cria o mapa Sentinel-2 NDVI e salva como HTML
            map_sentinel2 = create_map(ndvi_sentinel2.median(), visualization_ndvi_sentinel2, CENTRAL_POINTS, 6, "NDVI Sentinel-2")
            map_sentinel2.to_html('map_ndvi_sentinel2.html')

            # Salvar NDVI Sentinel-2 no Google Drive
            sentinel_image = ndvi_sentinel2.median().clip(caatinga)
            sentinel_task = ee.batch.Export.image.toDrive(
                image=sentinel_image,
                description=f'Sentinel_NDVI_Export_{timestamp}',
                folder=folder_drive,
                scale=scale,
                region=caatinga.geometry().bounds().getInfo()['coordinates'],
                fileFormat='GeoTIFF'
            )
            sentinel_task.start()
            tasks.append(sentinel_task)
        else:
            print("Nenhuma imagem Sentinel-2 disponível para o intervalo de tempo especificado.")

        # Monitoramento das tarefas
        # monitor_tasks(tasks)

    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
