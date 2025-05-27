# FIAP Tech Challenge Fase 3 - API para identificar instrumentos musicais com base na imagem.

## Desenho da Arquitetura

![WhatsApp_Image_2025-05-26_at_22 15 19](https://github.com/user-attachments/assets/3fabf81f-c008-4037-bd6e-8ab77e859742)


## Fonte dos dados 
Utilizamos o kaggle como fonte de dados das imagens de instrumentos

## EventBridge (CloudWatch Events)
Usamos o event bridge para acionar a função lambda diáriamente.

## Lambda - fiap_tc_3_getdata
A primeira função lambda tem como objetivo coletar diáriamente os dados da fonte na sua forma bruta, tratar os dados, retornar um arquivo JSON com 2 chaves, instrumento e imagem (imagem salva em base64), por fim armazena no bucket S3 pela data de extração.

```python
import os
import boto3
import json
import datetime
from datetime import datetime


# Configurações do S3
BUCKET_NAME = "tc3-postech-fiap-upda"
BASE_FOLDER = "base-zip"

# Nome do dataset Kaggle
DATASET = "nikolasgegenava/music-instruments"
LOCAL_ZIP = "music-instruments.zip"

def lambda_handler(event, context):
       
    config_dir = '/tmp/.kaggle'
    os.makedirs(config_dir, exist_ok=True)


    kaggle_json = {
        "username": os.environ['KAGGLE_USERNAME'],
        "key": os.environ['KAGGLE_KEY']
    }


    with open(os.path.join(config_dir, 'kaggle.json'), 'w') as f:
        json.dump(kaggle_json, f)

    
    os.environ['KAGGLE_CONFIG_DIR'] = config_dir
    import kaggle
    
    kaggle.api.authenticate()

    kaggle.api.dataset_download_files(DATASET, path="/tmp", quiet=False)
    
    local_path = f"/tmp/{LOCAL_ZIP}"
    today = datetime.today().strftime('%Y-%m-%d')

    s3_key = f"{BASE_FOLDER}/{today}/{LOCAL_ZIP}"

    # Passo 2: Subir para o S3
    s3 = boto3.client('s3')
    s3.upload_file(local_path, BUCKET_NAME, s3_key)

    return {
        "statusCode": 200,
        "body": f"Arquivo enviado para s3://{BUCKET_NAME}/{s3_key}"
    }


```

## Lambda - fiap_tc_3_create_table
Esta função é acionada sempre que um arquivo novo é adicionado no bucket S3. Após o termino do ETL o lambda extrai os arquivos JSON e incrementa na databesa no Athena.

```python
import boto3
import zipfile
import os
import io
import base64
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']


    response = s3.get_object(Bucket=bucket, Key=key)
    zip_bytes = response['Body'].read()

    # Lê o ZIP diretamente da memória
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        json_result = []

        for file_name in zip_file.namelist():
            if file_name.endswith('.jpg'):
                instrumento = file_name.split('/')[1]  # music_instruments/<instrumento>/<imagem>
                image_data = zip_file.read(file_name)
                encoded_image = base64.b64encode(image_data).decode('utf-8')

                json_result.append({
                    "instrumento": instrumento,
                    "imagem": encoded_image
                })

    # Opcional: salvar JSON gerado em outro local no S3
    json_key = key.replace(".zip", ".json").replace("base-zip", "base-json")
    s3.put_object(
        Bucket=bucket,
        Key=json_key,
        Body='\n'.join([json.dumps(obj) for obj in json_result]),
        ContentType='application/json'
    )

    athena = boto3.client('athena')

    # Parâmetros para Athena
    athena_output = "s3://tc3-postech-fiap-upda/athena-results/"
    json_s3_path = f"s3://{bucket}/{json_key}"
    database_name = "tc3-database" 
    table_name = "base_de_imagens"

    # Query para criar a tabela
    create_table_query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {table_name} (
    instrumento STRING,
    imagem STRING
    )
    ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
    WITH SERDEPROPERTIES (
    'serialization.format' = '1'
    )
    LOCATION '{json_s3_path.rsplit('/', 1)[0]}/'
    TBLPROPERTIES ('has_encrypted_data'='false');
    """

    # Executa a query no Athena
    response = athena.start_query_execution(
        QueryString=create_table_query,
        QueryExecutionContext={'Database': database_name},
        ResultConfiguration={'OutputLocation': athena_output}
    )

    return {
        "statusCode": 200,
        "body": f"JSON gerado com {len(json_result)} imagens e salvo em s3://{bucket}/{json_key}",
        "message": f"base de dados {database_name} criada com sucesso no athena"
    }

```
## Athena
Utilizado para armazenar a tabela relacional com os dados de treino do modelo.
![athena](https://github.com/user-attachments/assets/cc3f793c-3cfb-463e-81af-e793012a88e5)


