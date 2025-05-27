import streamlit as st
import requests
import base64
import json
# Aceita somente PNG ou JPG/JPEG
uploaded_file = st.file_uploader(
    "Escolha uma imagem PNG ou JPG",
    type=['png', 'jpg', 'jpeg']
)

if uploaded_file is not None:
    # Lê os bytes da imagem
    bytes_data = uploaded_file.getvalue()

    # Converte para base64
    base64_str = base64.b64encode(bytes_data).decode('utf-8')

    # Exibe a imagem
    st.image(uploaded_file, caption="Imagem enviada", use_container_width=True)
    headers = {
        "image_base64": base64_str
    }


    response = requests.post("http://13.59.118.223/predict-instrument/",json=headers,verify=False)
    #st.text_area("Imagem em Base64", response.text, height=200)
    classe = ""
    if '0' == json.loads(str(response.text))["classe"]:
        classe = "accordion"
    elif '1' == json.loads(str(response.text))["classe"]:
        classe = "banjo"
    elif '2' == json.loads(str(response.text))["classe"]:
        classe = "drum"
    elif '3' == json.loads(str(response.text))["classe"]:
        classe = "flute"
    elif '4' == json.loads(str(response.text))["classe"]:
        classe = "guitar"
    elif '5' == json.loads(str(response.text))["classe"]:
        classe = "harmonica"
    elif '6' == json.loads(str(response.text))["classe"]:
        classe = "saxophone"
    elif '7' == json.loads(str(response.text))["classe"]:
        classe = "sitar"
    elif '8' == json.loads(str(response.text))["classe"]:
        classe = "tabla"
    elif '9' == json.loads(str(response.text))["classe"]:
        classe = "violin"
    st.header( f"O instrumento enviado é um {classe}")