from fastapi import FastAPI  # HTTPException
import psycopg2
import openai
import os
from dotenv import load_dotenv
import uvicorn

# Criando a instância do FastAPI
app = FastAPI()

# Carregar variáveis do .env
load_dotenv(dotenv_path="D:\\Sadeck\\LLM_DETER\\OPENAI_API_KEY.env")  # Corrigindo a barra invertida
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))  # Para depuração
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = openai.OpenAI(api_key=api_key)

# Configuração do banco de dados
DB_CONFIG = {
    "dbname": "deterb",
    "user": "postgres",
    "password": "acessopgcra",
    "host": "localhost",
    "port": "5432",
}

def gerar_sql(pergunta: str) -> str:
    """Usa o ChatGPT para converter perguntas em SQL."""
    prompt = f"Transforme a seguinte pergunta em SQL: '{pergunta}'"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você gera consultas SQL para PostgreSQL/PostGIS."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Definição das rotas
@app.get("/")
def home():
    return {"message": "API funcionando!"}


# Executando o servidor
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

from pydantic import BaseModel

class PerguntaRequest(BaseModel):
    pergunta: str

@app.post("/gerar_sql")
def gerar_sql_endpoint(request: PerguntaRequest):
    """Recebe uma pergunta e retorna a consulta SQL gerada pelo OpenAI."""
    try:
        sql_query = gerar_sql(request.pergunta)
        return {"sql_query": sql_query}
    except Exception as e:
        return {"error": str(e)}
