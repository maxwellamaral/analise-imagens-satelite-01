import ee
import geemap
import time
import math
import datetime

# Função para exportar uma única imagem para o Google Drive
def export_image(image, description, folder, region, scale):
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region,
        scale=scale,
        fileFormat='GeoTIFF'
    )
    task.start()
    return task

# Função para calcular a escala com base na área (Redução para 500 Kp)
def calculate_scale(area_m2, max_pixels=5e6):
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
        # Define o período de tempo (inicio e fim)
        DATE_START = datetime.datetime(2017, 1, 1)
        DATE_END = datetime.datetime(2024, 1, 1)

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
        # Landsat 8 - Exportação de 2 imagens por mês
        # -------------------------------------------
        
        current_date = DATE_START

        while current_date < DATE_END:
            start_date = current_date.strftime('%Y-%m-%d')
            next_month = (current_date + datetime.timedelta(days=31)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')

            # Filtra as imagens Landsat 8 por mês
            datasetLangSat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterDate(start_date, end_date) \
                .filterBounds(caatinga) \
                .filter(ee.Filter.lt('CLOUD_COVER', CLOUDY_PIXEL_PERCENTAGE)) \
                .select(['SR_B5', 'SR_B4'])  # Seleciona apenas as bandas NIR e Red

            # Limita a 2 imagens por mês
            filtered_images = datasetLangSat  #.limit(2)
            landsat_count = filtered_images.size().getInfo()

            if landsat_count > 0:
                # Exporta cada uma das duas imagens de Landsat 8
                for i in range(landsat_count):
                    landsat_image = ee.Image(filtered_images.toList(landsat_count).get(i)).clip(caatinga)
                    landsat_task = export_image(
                        image=landsat_image,
                        description=f'Landsat_Image_{start_date}_{i}_{timestamp}',
                        folder=folder_drive,
                        region=caatinga.geometry().bounds().getInfo()['coordinates'],
                        scale=scale
                    )
                    tasks.append(landsat_task)

            current_date = next_month

        # -------------------------------------------
        # Sentinel-2 - Exportação de 2 imagens por mês
        # -------------------------------------------
        
        current_date = DATE_START

        while current_date < DATE_END:
            start_date = current_date.strftime('%Y-%m-%d')
            next_month = (current_date + datetime.timedelta(days=31)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')

            # Filtra as imagens Sentinel-2 por mês
            datasetSentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterDate(start_date, end_date) \
                .filterBounds(caatinga) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUDY_PIXEL_PERCENTAGE)) \
                .select(['B8', 'B4'])  # Seleciona apenas as bandas NIR e Red

            # Limita a 2 imagens por mês
            filtered_images = datasetSentinel2 #.limit(2)
            sentinel_count = filtered_images.size().getInfo()

            if sentinel_count > 0:
                # Exporta cada uma das duas imagens de Sentinel-2
                for i in range(sentinel_count):
                    sentinel_image = ee.Image(filtered_images.toList(sentinel_count).get(i)).clip(caatinga)
                    sentinel_task = export_image(
                        image=sentinel_image,
                        description=f'Sentinel_Image_{start_date}_{i}_{timestamp}',
                        folder=folder_drive,
                        region=caatinga.geometry().bounds().getInfo()['coordinates'],
                        scale=10  # Escala padrão para Sentinel-2
                    )
                    tasks.append(sentinel_task)

            current_date = next_month

        # Monitoramento das tarefas
        # monitor_tasks(tasks)

    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
