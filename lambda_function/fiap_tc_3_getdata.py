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

