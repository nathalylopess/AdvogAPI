# API para Advogados
## Visão Geral
API com webscraping integrado para capturar dados do sistema GPS-Jus do Tribunal de Justiça do Rio Grande do Norte (TJRN) (https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php).

## Instalação
1. Certifique-se de ter o Python instalado. Você pode baixar no site oficial [python.org](https://www.python.org/).
2. Clone o repositório git:
   ```bash
   https://github.com/camille-eloah/gpsjus-tjrn-webscraping.git
   ```
   
3. Acesse o diretório do projeto:
   
   ```bash
   cd gpsjus-tjrn-webscraping
   ```

5. Configure um ambiente virtual (recomendado):
 
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

5. Instale as dependências necessárias:

   ```bash
   pip install -r requirements.txt
   ```

6. Inicialize a aplicação via terminal:

   ```bash
    uvicorn app.main:app
   ```
