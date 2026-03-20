import requests

url = "https://tomesoft1.pythonanywhere.com/actualizar_caducidad_proveedores/"

try:
    response = requests.get(url, timeout=30)

    print("Status code:", response.status_code)
    print("Respuesta:")
    print(response.text)

except requests.exceptions.RequestException as e:
    print("Error en la solicitud:", e)