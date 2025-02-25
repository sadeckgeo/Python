import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Carregar as imagens TIFF usando rasterio
band2_path = "C:/Users/luis.sadeck.COEAM/Documents/DETER_teste/cbers9.dpi.inpe.br/AMAZONIA_1_WFI_20240521_038_016_L4_BAND2.tif"
band3_path = "C:/Users/luis.sadeck.COEAM/Documents/DETER_teste/cbers9.dpi.inpe.br/AMAZONIA_1_WFI_20240521_038_016_L4_BAND3.tif"
band4_path = "C:/Users/luis.sadeck.COEAM/Documents/DETER_teste/cbers9.dpi.inpe.br/AMAZONIA_1_WFI_20240521_038_016_L4_BAND4.tif"

with rasterio.open(band3_path) as band3:
    banda3 = band3.read(1)

with rasterio.open(band4_path) as band4:
    banda4 = band4.read(1)

# Criar DataFrame com as bandas
df = pd.DataFrame({
    'Banda3': banda3.flatten(),
    'Banda4': banda4.flatten()
})

# Remover valores NA
df = df.dropna()

# Visualizar os primeiros dados
print(df.head())

# Plotar os dados
plt.scatter(df['Banda3'], df['Banda4'])
plt.xlabel('Banda 3')
plt.ylabel('Banda 4')
plt.title('Dispersão Banda 3 vs Banda 4')
plt.show()