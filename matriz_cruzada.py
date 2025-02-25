import pandas as pd

# Caminho do arquivo
file_path = "D:/SADECK_DR/BASE/Validacao_base/Pts_validacao_finalizado/Pontos_Validados_f1.csv"

# Carregar os dados
df = pd.read_csv(file_path)

# Exibir as primeiras linhas para análise
df.head()

# Selecionar as colunas relevantes
class_columns = ['DSF_18', 'DSF_19', 'DSF_20', 'DSF_21', 'DSF_22', 'DSF_23', 'DSF_88_17', 'FLORESTA']
df_classes = df[class_columns].copy()
df_classes['class_name'] = df['class_name']

# Transformar os valores das classes mapeadas em formato binário (1 = presença, 0 = ausência)
df_classes[class_columns] = df_classes[class_columns].gt(0).astype(int)

# Criar a matriz cruzada (confusão)
conf_matrix = pd.crosstab(df_classes['class_name'], df_classes[class_columns].idxmax(axis=1))

# Exibir a matriz de confusão
print (conf_matrix)

# Calcular os erros do produtor, consumidor e a acurácia global

# Totais por classe (Linhas e Colunas)
total_por_linha = conf_matrix.sum(axis=1)  # Total de amostras reais por classe
total_por_coluna = conf_matrix.sum(axis=0)  # Total de amostras preditas por classe
diagonal = conf_matrix.values.diagonal()  # Valores corretos (diagonal)

# Erro do Produtor (Omissão)
erro_produtor = 1 - (diagonal / total_por_linha)

# Erro do Consumidor (Comissão)
erro_consumidor = 1 - (diagonal / total_por_coluna)

# Acurácia Global
acuracia_global = diagonal.sum() / conf_matrix.values.sum()

# Criar um DataFrame com os resultados
metricas_df = pd.DataFrame({
    'Erro do Produtor': erro_produtor,
    'Erro do Consumidor': erro_consumidor
}, index=conf_matrix.index)

# Adicionar a acurácia global
metricas_df.loc['Acurácia Global'] = acuracia_global

# Exibir os resultados
print(metricas_df)
