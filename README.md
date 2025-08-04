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
docker compose up
```

### Manual
***Pré-requisitos:***
* Google Chrome
* Chrome Driver
* Python 3.9 ou superior
  
1. Verifique se o Python está instalado. Você pode baixar no site oficial [python.org](https://www.python.org/).
   ```bash
   python --version
   ```
   
3. Clone o repositório git e acesse o diretório do projeto:
   ```bash
   https://github.com/nathalylopess/AdvogAPI.git
   cd AdvogAPI
   ```

4. Configure um ambiente virtual (recomendado):
 
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
      
## Autenticação
Para conseguir utilizar a API, é necessário criar um usuário e autenticar-se.

### Criando usuário

1. Clique na rota `POST /api/v1/auth/usuarios Criar novo usuário`
<img width="1127" height="297" alt="Image" src="https://github.com/user-attachments/assets/4718f974-96bb-4b80-8db7-bb34e499f741" />

2. Clique no botão `Try it out`
<img width="1127" height="407" alt="Image" src="https://github.com/user-attachments/assets/dd1ecde9-ac8f-4b90-968e-429d60da73a5" />

3. Modifique os valores das chaves **username** (nome de usuário) e **password** (senha). No exemplo abaixo, o nome de usuário é `admin` e a senha é `123`. Mantenha o campo **disabled** como `false`.
<img width="1127" height="892" alt="Image" src="https://github.com/user-attachments/assets/1250b19c-238a-417a-8d39-fb962b9234c4" />

4. Clique em Execute. Você obterá uma resposta semelhante a esta:
<img width="1122" height="818" alt="Image" src="https://github.com/user-attachments/assets/ca28a59b-44a6-4bae-a790-a5439f9339b1" />

### Autenticando-se

1. Clique no botão Authorize
<img width="1122" height="618" alt="Image" src="https://github.com/user-attachments/assets/3fc50b33-c396-4a93-86c1-9b9ef57d2629" />

2. Insira as credenciais "username" e "password" cadastradas e clique em "Authorize" novamente
<img width="1122" height="814" alt="Image" src="https://github.com/user-attachments/assets/04efbbf0-73c1-4635-9d75-94d4aa9e2e3d" />

3. Clique em "Close" e você estará pronto para utilizar a API.
<img width="1122" height="814" alt="Image" src="https://github.com/user-attachments/assets/04686061-8e77-4057-9c88-32278d35e4e5" />

### Usando Insomnia

Após executar a API, você pode utilizar também outras interfaces para testá-la, como Insomnia. É especialmente útil para consultar rotas mais pesadas, como a rota `GET /api/v1/unidades`. Basta criar no header (cabeçalho) uma chave **Authorization** com o valor `bearer <seu_token_gerado>`.

<img width="1916" height="900" alt="Image" src="https://github.com/user-attachments/assets/af3b0c27-3c78-452f-802d-8e9b358ebded" />



