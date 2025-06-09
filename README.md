# API para Advogados
## Visão Geral
API com webscraping integrado para capturar dados do sistema GPS-Jus do Tribunal de Justiça do Rio Grande do Norte (TJRN) (https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php).

## Instalação
### Dockerfile
***Pré-requisitos:***
* Docker
* Docker Compose
1. Clone o repositório git e acesse o diretório do projeto:
```bash
git clone https://github.com/nathalylopess/AdvogAPI.git
cd AdvogAPI
```

2. Inicie os containers:
```bash
docker compose up --build
```

3. Acesse a aplicação na seguinte URL:
`http://localhost:8000`

4. Nas próximas vezes que for levantar o container, execute apenas com o comando abaixo
```bash
docker compose up```

### Manual
1. Certifique-se de ter o Python instalado. Você pode baixar no site oficial [python.org](https://www.python.org/).
2. Clone o repositório git e acesse o diretório do projeto:
   ```bash
   https://github.com/nathalylopess/AdvogAPI.git
   cd AdvogAPI
   ```

3. Configure um ambiente virtual (recomendado):
 
   ```bash
   python -m venv venv
   ```

e ative o ambiente virtual

  - No Windows:
    
   ```bash
   venv\Scripts\activate
   ```

  - No Linux:
    
   ```bash
   source venv/bin/activate
   ```

4. Instale as dependências necessárias:

   ```bash
   pip install -r requirements.txt
   ```

5. Inicialize a aplicação via terminal:

   ```bash
    uvicorn app.main:app
   ```

6. Caso queira obter os dados atualizados, execute o web scraper para iniciar a coleta:
   ```bash
   python -m app.scripts.run_scraper
   ```
      
