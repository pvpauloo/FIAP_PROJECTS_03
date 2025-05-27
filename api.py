from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
from io import BytesIO
from tensorflow.keras.preprocessing.image import load_img
from PIL import UnidentifiedImageError
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np
import pickle
import boto3

### Dowload model from s3
conn = boto3.resource('s3')  # again assumes boto.cfg setup, assume AWS S3
bucket = conn.Bucket('tc3-postech-fiap-upda')


with open('instruments.pickle', 'wb') as data:
    bucket.download_fileobj('model/instruments.pickle', data)


with open('instruments.pickle', 'rb') as f:
    final_model = pickle.load(f)

#####

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# Pydantic model for the payload
class ImagePayload(BaseModel):
    image_base64: str

@app.post("/upload-image/")
async def upload_image(payload: ImagePayload):
    try:
        # Clean possible data URI prefix
        base64_data = payload.image_base64.split(",")[-1]

        # Decode and wrap in file-like object
        image_bytes = base64.b64decode(base64_data)
        image_file = BytesIO(image_bytes)

        # Load the image using keras
        img = load_img(image_file, target_size=(224, 224))  # adjust size if needed

        # (Optional) Convert to array or do further processing
        # img_array = img_to_array(img)

        return {"message": "Image loaded successfully", "size": img.size}

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading image: {str(e)}")


@app.post("/predict-instrument/")
async def upload_image(payload: ImagePayload):
    try:
        # Clean possible data URI prefix
        base64_data = payload.image_base64.split(",")[-1]

        # Decode and wrap in file-like object
        image_bytes = base64.b64decode(base64_data)
        image_file = BytesIO(image_bytes)

        # Load the image using keras
        img = image.load_img(image_file, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        pred = final_model.predict(img_array)

        # (Optional) Convert to array or do further processing
        # img_array = img_to_array(img)

        return {"message": f'A classe prevista é: {np.argmax(pred)}',
                "classe": "{}".format(np.argmax(pred))}

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading image: {str(e)}")