import ee
import geemap
import time
import math
import datetime 

# Função para aplicar fatores de escala
def apply_scale_factors(image):
    optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)

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

# Função para criar mapa (não alterado)
def create_map(dataset, visualization, center_coords, zoom_level, map_name):
    m = geemap.Map()
    m.set_center(*center_coords, zoom_level)
    m.addLayer(dataset, visualization, map_name)
    return m

# Função para calcular a escala com base na área
# Redução para 50 Mp (5e7 pixels). Limite do GEE.
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
        # Landsat 8
        # -------------------------------------------
        
        # Coleção Landsat 8
        datasetLangSat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterDate(DATE_START_LANGSAT, DATE_END_LANGSAT) \
            .filterBounds(caatinga) \
            .filter(ee.Filter.lt('CLOUD_COVER', CLOUDY_PIXEL_PERCENTAGE)) \
            .map(apply_scale_factors)
            
        visualizationLangSat = {
            'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
            'min': 0.0,
            'max': 0.3,
        }

        # Cria o mapa Landsat e salva como HTML
        map_landsat = create_map(datasetLangSat, visualizationLangSat, CENTRAL_POINTS, 6, "True Color (432)")
        map_landsat.to_html('map_landsat.html')

        # Salvar Landsat no Google Drive
        landsat_image = datasetLangSat.median().clip(caatinga)
        landsat_task = ee.batch.Export.image.toDrive(
            image=landsat_image,
            description=f'Landsat_Export_{timestamp}',
            folder=folder_drive,
            scale=scale,
            region=caatinga.geometry().bounds().getInfo()['coordinates'],
            fileFormat='GeoTIFF'
        )
        landsat_task.start()
        tasks.append(landsat_task)
        

        # -------------------------------------------
        # Sentinel-2
        # -------------------------------------------
        
        # Coleção Sentinel-2
        datasetSentinel2 = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(DATE_START_SENTINEL, DATE_END_SENTINEL)
            .filterBounds(caatinga)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUDY_PIXEL_PERCENTAGE))
            .map(mask_s2_clouds)
        )
        
        visualizationSentinel2 = {
            'min': 0.0,
            'max': 0.3,
            'bands': ['B4', 'B3', 'B2'],
        }

        # Cria o mapa Sentinel-2 e salva como HTML
        map_sentinel2 = create_map(datasetSentinel2.mean(), visualizationSentinel2, CENTRAL_POINTS, 6, "RGB")
        map_sentinel2.to_html('map_sentinel2.html')

        # Salvar Sentinel-2 no Google Drive
        sentinel_image = datasetSentinel2.median().clip(caatinga)
        sentinel_task = ee.batch.Export.image.toDrive(
            image=sentinel_image,
            description=f'Sentinel_Export_{timestamp}',
            folder=folder_drive,
            scale=scale,
            region=caatinga.geometry().bounds().getInfo()['coordinates'],
            fileFormat='GeoTIFF'
        )
        sentinel_task.start()
        tasks.append(sentinel_task)

        # Monitoramento das tarefas
        monitor_tasks(tasks)
    
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
