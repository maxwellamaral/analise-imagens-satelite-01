import ee
ee.Authenticate()  # Inicia o processo de autenticação (com force=True ele força a reautenticação)
ee.Initialize(project='analise-satelite-projeto-01')    # Inicializa a sessão do GEE
