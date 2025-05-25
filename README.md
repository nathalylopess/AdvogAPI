# Webscraping das Unidades Judiciárias do Gerencial da Vara 
## Visão Geral
Script de webscraping para capturar dados do sistema GPS-Jus do Tribunal de Justiça do Rio Grande do Norte (TJRN) (https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php) e exportar em formato de tabela.

## Instalação
1. Certifique-se de ter o Python instalado. Você pode baixar no site oficial [python.org](https://www.python.org/).
2. Clone o repositório git:
   
   ```git clone https://github.com/camille-eloah/gpsjus-tjrn-webscraping.git```
   
3. Acesse o diretório do projeto:
   
```cd gpsjus-tjrn-webscraping```

4. Configure um ambiente virtual (recomendado):
 
```python -m venv venv```

e ative o ambiente virtual

  - No Windows:
    
```bash
.\venv\Scripts\Activate.ps1
```

  - No Linux:
    
```bash
source venv/bin/activate
```

5. Instale as dependências necessárias:

```bash
    pip install -r requirements.txt
```

6. Execute o Script via terminal:

```bash
    python script.py
```