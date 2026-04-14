import json

import requests


def test_prea_a2a():
    url = "https://prea-backend-f064af73127b.herokuapp.com/api/a2a"

    # JSON-RPC 2.0 message structure for A2A
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "text": "Hola PREA, soy fu7ur3pr00f. ¿Me recibís?",
            "context": {
                "source": "fu7ur3pr00f-agent",
                "intent": "interoperability-test",
            },
        },
        "id": 1,
    }

    print(f"Enviando peticion A2A a {url}...")
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Respuesta de PREA:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error de conexion: {e}")


if __name__ == "__main__":
    test_prea_a2a()
