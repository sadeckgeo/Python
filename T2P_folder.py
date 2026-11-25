import re
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Defina apenas a pasta onde estão as tabelas e a pasta onde salvar os .gpkg
pasta_entrada = Path(r"D:/Sadeck/EMPRESA/PETROBRAS_UFPA/Dados")
pasta_saida = Path(r"d:/Sadeck/EMPRESA/PETROBRAS_UFPA/Dados/Saida_GPKG")
pasta_saida.mkdir(parents=True, exist_ok=True)  # Cria a pasta de saída se não existir

# Extensões de tabelas que o script vai procurar
extensoes_validas = {".csv", ".txt", ".tsv", ".xlsx", ".xls"}

# Funções auxiliares (definidas uma única vez fora do loop)
possiveis_lon = ["decimallongitude", "longitude", "long", "lon", "coord_x", "x", "este", "easting", "Decimallongitude(WGS84)"]
possiveis_lat = ["decimallatitude", "latitude", "lat", "coord_y", "y", "norte", "northing", "Decimallatitude(WGS84)"]

def encontrar_coluna(df, candidatos):
    # Normaliza os nomes das colunas removendo espaços, parênteses e caracteres especiais
    # Ex: "Decimal longitude (WGS84)" vira "decimallongitudewgs84"
    mapa_cols = {
        re.sub(r"[^a-z0-9]", "", col.lower()): col 
        for col in df.columns
    }
    
    # 1ª tentativa: correspondência exata após limpar caracteres especiais
    for cand in candidatos:
        cand_limpo = re.sub(r"[^a-z0-9]", "", cand.lower())
        if cand_limpo in mapa_cols:
            return mapa_cols[cand_limpo]
            
    # 2ª tentativa: busca parcial (pega "Decimal longitude (WGS84)" porque começa com "decimallongitude")
    for cand in candidatos:
        cand_limpo = re.sub(r"[^a-z0-9]", "", cand.lower())
        if len(cand_limpo) >= 3:  # Evita falsos positivos com letras soltas como 'x' ou 'y'
            for col_limpa, col_original in mapa_cols.items():
                if cand_limpo in col_limpa:
                    return col_original

    raise KeyError(f"Coluna de coordenada não encontrada. Disponíveis: {list(df.columns)}")

def converter_para_decimal(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip().upper().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        pass

    sinal = -1 if re.search(r"[SWO-]", texto) else 1
    numeros = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", texto)]

    if len(numeros) == 1:
        decimal = numeros[0]
    elif len(numeros) == 2:
        decimal = numeros[0] + (numeros[1] / 60.0)
    elif len(numeros) >= 3:
        decimal = numeros[0] + (numeros[1] / 60.0) + (numeros[2] / 3600.0)
    else:
        return None

    return sinal * decimal

# Busca todos os arquivos da pasta com as extensões desejadas
arquivos = [f for f in pasta_entrada.iterdir() if f.is_file() and f.suffix.lower() in extensoes_validas]
print(f"Encontrados {len(arquivos)} arquivo(s) para processar.\n" + "-"*50)

# Loop principal: processa um arquivo por vez
for caminho_arquivo in arquivos:
    print(f"Processando: {caminho_arquivo.name}...")
    try:
        # 1. Leitura inteligente
        if caminho_arquivo.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(caminho_arquivo)
        else:
            try:
                df = pd.read_csv(caminho_arquivo, sep=None, engine="python", encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(caminho_arquivo, sep=None, engine="python", encoding="latin1")

        df.columns = df.columns.str.strip()

        # 2. Detecção automática das colunas
        col_lon_original = encontrar_coluna(df, possiveis_lon)
        col_lat_original = encontrar_coluna(df, possiveis_lat)

        # 3. Padronização das coordenadas
        df["decimalLongitude"] = df[col_lon_original].apply(converter_para_decimal)
        df["decimalLatitude"] = df[col_lat_original].apply(converter_para_decimal)

        df_valido = df.dropna(subset=["decimalLongitude", "decimalLatitude"]).copy()
        df_valido = df_valido[
            (df_valido["decimalLongitude"].between(-180, 180)) &
            (df_valido["decimalLatitude"].between(-90, 90))
        ]

        if df_valido.empty:
            print(f"  [AVISO] Nenhum ponto válido encontrado em {caminho_arquivo.name}. Pulando.\n")
            continue

        # 4. Criação do GeoDataFrame (mude para .to_crs("EPSG:4674") se quiser SIRGAS 2000)
        gdf = gpd.GeoDataFrame(
            df_valido,
            geometry=gpd.points_from_xy(df_valido["decimalLongitude"], df_valido["decimalLatitude"]),
            crs="EPSG:4326"
        )

        # 5. Exportação dinâmica: usa o mesmo nome do arquivo original (stem) com extensão .gpkg
        saida_gpkg = pasta_saida / f"{caminho_arquivo.stem}.gpkg"
        gdf.to_file(saida_gpkg, layer="pontos", driver="GPKG")

        print(f"  [OK] {len(gdf)} pontos salvos em: {saida_gpkg.name}\n")

    except Exception as erro:
        # Se um arquivo der erro, avisa no terminal e continua para o próximo sem travar tudo
        print(f"  [ERRO] Falha ao processar {caminho_arquivo.name}: {erro}\n")

print("Processamento em lote finalizado!")