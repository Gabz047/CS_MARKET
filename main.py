import requests

## Consome o Web Service REST (a resposta vem em JSON) e monta a lista de produtos
def get_market_data():
    lista = []
    try:
        url = "https://market.csgo.com/api/v2/prices/RUB.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        for item in data["items"]:
            produto = {}
            produto["market_hash_name"] = item["market_hash_name"]
            produto["volume"] = int(item["volume"])
            produto["price"] = float(item["price"])
            lista.append(produto)
    except requests.RequestException as e:
        print("Erro ao carregar os produtos:", e)
        lista = []
    except (KeyError, ValueError):
        print("Erro: a resposta da API veio em formato inesperado")
        lista = []
    return lista


products = get_market_data()

## Carrinho: nome do produto -> {"Nome", "Quantidade", "Preco"}
shopping_cart = {}
money = 1000
PAGE_SIZE = 10


## Procura um produto pelo nome (ignora maiúsculas e espaços nas pontas)
def find_product(name, userAction=False):
    name = name.strip().lower()
    for product in products:
        if product["market_hash_name"].lower() == name:
            return product
    return None


## Procura o nome de um item dentro do carrinho (ignora maiúsculas)
def find_in_cart(name):
    name = name.strip().lower()
    for key in shopping_cart:
        if key.lower() == name:
            return key
    return None


## Lista até 5 produtos cujo nome contém o texto digitado
def suggest_products(name):
    text = name.strip().lower().strip("'\"")
    suggestions = []
    if text != "":
        for product in products:
            if len(suggestions) < 5 and text in product["market_hash_name"].lower():
                suggestions.append(product["market_hash_name"])
    return suggestions


def add_to_cart(item, quantity):
    product = find_product(item)
    if product is None:
        result = {"erro": f"{item} não encontrado nos produtos", "carrinho": shopping_cart}
        suggestions = suggest_products(item)
        if len(suggestions) > 0:
            result["você quis dizer"] = suggestions
        return result
    if quantity <= 0:
        return {"erro": "A quantidade deve ser maior que zero", "carrinho": shopping_cart}

    name = product["market_hash_name"]
    in_cart = 0
    if name in shopping_cart:
        in_cart = shopping_cart[name]["Quantidade"]
    if product["volume"] < in_cart + quantity:
        return {"erro": f"Estoque insuficiente para {name} | Estoque do produto: {product['volume']}", "carrinho": shopping_cart}

    if name in shopping_cart:
        shopping_cart[name]["Quantidade"] = in_cart + quantity
    else:
        shopping_cart[name] = {"Nome": name, "Quantidade": quantity, "Preco": product["price"]}
    return {"mensagem": f"{name} adicionado ao carrinho", "carrinho": shopping_cart}


def remove_from_cart(item):
    name = find_in_cart(item)
    if name is None:
        return {"erro": f"{item} não encontrado no carrinho", "carrinho": shopping_cart}
    del shopping_cart[name]
    return {"mensagem": f"{name} removido do carrinho", "carrinho": shopping_cart}


## Define a nova quantidade de um item do carrinho (0 remove o item)
def update_quantity(item, quantity):
    name = find_in_cart(item)
    if name is None:
        return {"erro": f"{item} não encontrado no carrinho", "carrinho": shopping_cart}
    if quantity < 0:
        return {"erro": "A quantidade não pode ser negativa", "carrinho": shopping_cart}
    if quantity == 0:
        return remove_from_cart(name)
    if find_product(name)["volume"] < quantity:
        return {"erro": f"Estoque insuficiente para {name} | Estoque do produto: {find_product(name)['volume']}", "carrinho": shopping_cart}

    shopping_cart[name]["Quantidade"] = quantity
    return {"mensagem": f"Quantidade de {name} atualizada para {quantity}", "carrinho": shopping_cart}


## Mostra cada item do carrinho com o subtotal, depois o total e o saldo
def show_cart():
    if len(shopping_cart) == 0:
        print("O carrinho está vazio.")
    else:
        total = 0
        number = 1
        for entry in shopping_cart.values():
            subtotal = entry["Preco"] * entry["Quantidade"]
            total = total + subtotal
            print(f"{number}. {entry['Nome']} | Quantidade: {entry['Quantidade']} | "
                  f"Preço un.: {entry['Preco']} | Subtotal: {round(subtotal, 2)}")
            number = number + 1
        print(f"Total: {round(total, 2)} | Saldo: {round(money, 2)} | Saldo restante: {round(money - total, 2)}")

## Finaliza a compra, atualiza o saldo e o estoque, e limpa o carrinho
def checkout():
    global money
    if len(shopping_cart) == 0:
        return {"erro": "O carrinho está vazio", "dinheiro": money, "carrinho": shopping_cart}

    total_cost = 0
    for entry in shopping_cart.values():
        total_cost = total_cost + entry["Preco"] * entry["Quantidade"]

    if total_cost > money:
        return {"erro": "Saldo insuficiente", "dinheiro": round(money, 2), "total do carrinho": round(total_cost, 2), "carrinho": shopping_cart}

    money = money - total_cost
    for name in shopping_cart:
        product = find_product(name)
        product["volume"] = product["volume"] - shopping_cart[name]["Quantidade"]
    shopping_cart.clear()
    return {"mensagem": "Compra finalizada com sucesso", "dinheiro": round(money, 2), "carrinho": shopping_cart}


## Retorna os produtos cujo nome contém o texto da busca
def search(query):
    query = query.strip().lower()
    found = []
    for product in products:
        if query in product["market_hash_name"].lower():
            found.append(product)
    return found


## Mostra a quantidade registrada em PAGE_SIZE de produtos por vez e pergunta se o usuário quer ver mais
def show_paginated(results):
    total = len(results)
    if total == 0:
        print("Nenhum produto encontrado.")
    else:
        continuar = True
        for start in range(0, total, PAGE_SIZE):
            if continuar:
                end = start + PAGE_SIZE
                if end > total:
                    end = total
                for i in range(start, end):
                    product = results[i]
                    print(f"{i + 1}. {product['market_hash_name']} | "
                          f"Estoque: {product['volume']} | Preço: {product['price']}")
                print(f"Mostrando {end} de {total}")
                if end < total:
                    resposta = input("Ver mais? (s/n): ")
                    if resposta.strip().lower() != "s":
                        continuar = False


def main():
    print("Bem-vindo ao Mercado!")
    running = True
    while running:
        action = input("Digite a ação (add, remove, update, cart, checkout, search, list, exit): ")
        if action == "exit":
            running = False
        elif action == "add" or action == "update":
            item = input("Digite o nome do item: ")
            if action == "add":
                prompt = "Digite a quantidade: "
            else:
                prompt = "Digite a nova quantidade (0 remove o item): "
            try:
                quantity = int(input(prompt))
                if action == "add":
                    print(add_to_cart(item, quantity))
                else:
                    print(update_quantity(item, quantity))
            except ValueError:
                print({"erro": "A quantidade deve ser um número inteiro"})
        elif action == "remove":
            item = input("Digite o nome do item: ")
            print(remove_from_cart(item))
        elif action == "search":
            query = input("Digite o termo da busca: ")
            show_paginated(search(query))
        elif action == "list":
            show_paginated(products)
        elif action == "cart":
            show_cart()
        elif action == "checkout":
            print(checkout())
        else:
            print({"erro": "Ação inválida"})


main()
