import boto3
import zipfile
import os
import io
import base64
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Pega os dados do evento S3 (objeto que disparou o trigger)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    #bucket = "tc3-postech-fiap-upda"
    #key = "base-zip/2025-05-24/music-instruments.zip"

    # Baixa o .zip do S3 para a memória
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
