import re
import pandas as pd
import geopandas as gpd

caminho_arquivo = r"d:/Sadeck/EMPRESA/PETROBRAS_UFPA/Dados/0026766-260928105237408_TotalEnergie_MeioFauna_AP.csv"

# 1. Leitura inteligente (CSV/TXT ou Excel)
if caminho_arquivo.lower().endswith((".xlsx", ".xls")):
    df = pd.read_excel(caminho_arquivo)
else:
    try:
        df = pd.read_csv(caminho_arquivo, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(caminho_arquivo, sep=None, engine="python", encoding="latin1")

df.columns = df.columns.str.strip()

# 2. Detecção automática dos nomes das colunas de Latitude e Longitude
possiveis_lon = ["decimallongitude", "longitude", "long", "lon", "coord_x", "x", "este", "easting"]
possiveis_lat = ["decimallatitude", "latitude", "lat", "coord_y", "y", "norte", "northing"]

def encontrar_coluna(df, candidatos):
    mapa_cols = {col.lower(): col for col in df.columns}
    for cand in candidatos:
        if cand in mapa_cols:
            return mapa_cols[cand]
    raise KeyError(f"Nenhuma coluna de coordenada encontrada entre: {candidatos}. Colunas disponíveis: {list(df.columns)}")

col_lon_original = encontrar_coluna(df, possiveis_lon)
col_lat_original = encontrar_coluna(df, possiveis_lat)

print(f"Colunas detectadas -> Longitude: '{col_lon_original}' | Latitude: '{col_lat_original}'")

# 3. Conversor universal de coordenadas (Decimal, DMS, DDM, Hemisférios N/S/E/W/O)
def converter_para_decimal(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip().upper().replace(",", ".")

    # Caso 1: Já é número decimal simples (ex: "-1.4558" ou "51.4821")
    try:
        return float(texto)
    except ValueError:
        pass

    # Detecta hemisfério ou sinal negativo (S, W, O de Oeste ou sinal '-')
    sinal = -1 if re.search(r"[SWO-]", texto) else 1

    # Extrai todos os blocos numéricos (Graus, Minutos, Segundos)
    numeros = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", texto)]

    if len(numeros) == 1:
        # Ex: "1.4558° S" ou "51.4821 W"
        decimal = numeros[0]
    elif len(numeros) == 2:
        # Graus e Minutos Decimais (ex: 01° 27.348' S)
        decimal = numeros[0] + (numeros[1] / 60.0)
    elif len(numeros) >= 3:
        # Graus, Minutos e Segundos (ex: 01° 27' 20.88" S)
        decimal = numeros[0] + (numeros[1] / 60.0) + (numeros[2] / 3600.0)
    else:
        return None

    return sinal * decimal

# Padroniza criando/atualizando as colunas oficiais Darwin Core (decimalLongitude / decimalLatitude)
df["decimalLongitude"] = df[col_lon_original].apply(converter_para_decimal)
df["decimalLatitude"] = df[col_lat_original].apply(converter_para_decimal)

# Filtra registros inválidos ou fora dos limites geográficos globais
antes = len(df)
df_valido = df.dropna(subset=["decimalLongitude", "decimalLatitude"]).copy()
df_valido = df_valido[
    (df_valido["decimalLongitude"].between(-180, 180)) &
    (df_valido["decimalLatitude"].between(-90, 90))
]
descartados = antes - len(df_valido)
if descartados > 0:
    print(f"Aviso: {descartados} registro(s) ignorado(s) por coordenadas vazias ou inválidas.")

# 4. Cria o GeoDataFrame mantendo todas as colunas originais + padronizadas
gdf = gpd.GeoDataFrame(
    df_valido,
    geometry=gpd.points_from_xy(df_valido["decimalLongitude"], df_valido["decimalLatitude"]),
    crs="EPSG:4326"
)

# 5. Exporta para GeoPackage (.gpkg)
saida_gpkg = r"d:\Sadeck\EMPRESA\PETROBRAS_UFPA\Dados\TotalEnergie_MeioFauna_AP.gpkg"
gdf.to_file(saida_gpkg, layer="pontos", driver="GPKG")

print(f"Sucesso! {len(gdf)} registros exportados para {saida_gpkg}")