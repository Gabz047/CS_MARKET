import requests


def get_market_data():
    """Retorna a lista de produtos do mercado.

    Cada produto é um dict com as chaves 'market_hash_name' (str),
    'volume' (int) e 'price' (float).
    Levanta requests.RequestException se a requisição falhar.
    """
    url = "https://market.csgo.com/api/v2/prices/RUB.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return [
        {
            "market_hash_name": item["market_hash_name"],
            "volume": int(item["volume"]),
            "price": float(item["price"]),
        }
        for item in data["items"]
    ]
