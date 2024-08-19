"""
Tarefas:

1. Aquisição de Dados: Utilizar o Google Earth Engine para acessar e baixar imagens de satélite da missão Landsat 8 e Sentinel-2 (estudá-las!), da região da Caatinga, desde 2017.
2. Pré-processamento: Realizar o cálculo do NDVI para todas as imagens adquiridas.
3. Análise Temporal: Desenvolver uma análise temporal da evolução do NDVI na região, identificando áreas de possível degradação florestal ao longo do tempo.
4. Mapeamento de Áreas Degradadas: Utilizando imagens do MapBiomas e o  Fragstat, mapear as áreas que apresentam aumento significativo do índice de fragmentação de floresta durante o período estudado. Repita utilizando agora imagens da Scene Classification Layer (SCL) do Sentinel-2 para o cálculo do índice de fragmentação do Fragstat.
5. Relatório: Elaborar um relatório técnico que inclua todos os passos realizados, as metodologias aplicadas, os resultados obtidos e uma discussão sobre a relevância dos achados.
"""

import ee
import geemap
# import streamlit as st
from init import GEE

# Classe base para aquisição de dados de satélite
class Satellite:
    def __init__(self, data_start: str, data_end: str, satellite: str, cloudy_pixel_percentage: int = 20):
        self.dataset = (
            ee.ImageCollection(satellite)
            .filterDate(data_start, data_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloudy_pixel_percentage))
        )

    def add_filter(self, filter_func):
        self.dataset = self.dataset.map(filter_func)
        return self

    def get_visualization(self, bands: list, min_value: float, max_value: float):
        return {"bands": bands, "min": min_value, "max": max_value}

# Classe para dados do LandSat8
class LandSat8(Satellite):
    def __init__(self, data_start: str, data_end: str, cloudy_pixel_percentage: int = 20):
        super().__init__(data_start, data_end, "LANDSAT/LC08/C02/T1_L2", cloudy_pixel_percentage)

    @staticmethod
    def apply_scale_factors(image):
        optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
        thermal_bands = image.select("ST_B.*").multiply(0.00341802).add(149.0)
        return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)

# Classe para dados do Sentinel2
class Sentinel2(Satellite):
    def __init__(self, data_start: str, data_end: str, cloudy_pixel_percentage: int = 20):
        super().__init__(data_start, data_end, "COPERNICUS/S2_SR_HARMONIZED", cloudy_pixel_percentage)

    @staticmethod
    def mask_s2_clouds(image):
        qa = image.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        return image.updateMask(mask).divide(10000)

def main():
    gee = GEE()
    ee.Initialize(gee.credentials)

    # Inicializa as coleções de imagens
    datasetLandSat = LandSat8("2021-05-01", "2021-06-01").add_filter(LandSat8.apply_scale_factors)
    datasetSentinel2 = Sentinel2("2020-05-01", "2020-06-01").add_filter(Sentinel2.mask_s2_clouds)

    # Parâmetros de visualização
    visualizationLandSat = datasetLandSat.get_visualization(["SR_B4", "SR_B3", "SR_B2"], 0.0, 0.3)
    visualizationSentinel2 = datasetSentinel2.get_visualization(["B4", "B3", "B2"], 0.0, 0.3)

    # Exibe os mapas
    m = geemap.Map()
    m.set_center(-114.2579, 38.9275, 8)
    m.addLayer(datasetLandSat.dataset, visualizationLandSat, "True Color (432)")
    m.to_html('map_landsat.html')

    m.set_center(83.277, 17.7009, 12)
    m.addLayer(datasetSentinel2.dataset.mean(), visualizationSentinel2, 'RGB')
    m.to_html('map_sentinel2.html')

if __name__ == "__main__":
    main()
