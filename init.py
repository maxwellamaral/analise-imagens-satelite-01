import ee


class GEE:
    def __init__(self):
        self.service_account = (
            "analise-satelite@analise-satelite-projeto-01.iam.gserviceaccount.com"
        )
        self.credentials = ee.ServiceAccountCredentials(
            self.service_account, ".analise-satelite-projeto-01-e926fdb56ea9.json"
        )
