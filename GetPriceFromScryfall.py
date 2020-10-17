import json
import time
import webbrowser

from requests import Session
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    print("Tqdm not found, please install it.")
    def tqdm(iterable):
        print(len(iterable))
        return iterable


SCRYFALL_API = "https://api.scryfall.com/cards/named?exact="


def get_scryfall_prices(lista, price_dict=None):
    """

    :param lista: iterable of cards[str]
    :param price_dict: pass prices dict to avoid scraping the same card twice
    :return: dict {card: {"usd": str, "usd_foil": str, "eur": str, "tix": str}, ...}
    """
    if price_dict is None:
        price_dict = dict()
    try:
        with Session() as s:
            for staple in tqdm(lista):
                if staple in price_dict:
                    print(staple, " is already in prices!")
                elif staple.lower() not in ("plains", "swamp", "mountain", "forest", "island"):
                    connection = s.get(SCRYFALL_API + staple.replace(" ", "+"))
                    if connection.status_code != 200:
                        print("CONNECTION ERROR:", connection.status_code)
                        break
                    resp = connection.json()
                    price_dict[staple] = resp["prices"]
                    # print(resp["prices"])
                    time.sleep(0.5)
    except Exception as e:
        print(e)
        safety_file = "safety_valve.json"
        with open(safety_file, "w") as s:
            json.dump(price_dict, s)
        print("Prices already scraped have been saved to", safety_file) 
    return price_dict


def decompose(dict_prices: dict, param: str, file: str, fill_errors_by_hand: bool = False)-> dict:
    """
    Return dict of specific type of prices from dict_prices with many different prices and save dict to file.
    If fill_errors_by_hand is True, open browser on the right eshop page and accept input from user for missing prices.
    
    :param dict_prices: dict of cards with multiple prices {card: {"usd": str, "usd_foil": str, "eur": str, "tix": str}, ...}
    :param param: key of dict to extract (e.g.: "eur" or "usd")
    :param file: json file path were to save result
    :param fill_errors_by_hand: set to True to add prices by hand. The function will automatically open the browser to the right eshop page so that the 
    :return: dict {"Mox Opal": 35.0, ...}
    """
    res = dict()
    errors = list()
    for card in tqdm(dict_prices):
        if card.lower() not in ("plains", "swamp", "mountain", "forest", "island"):
            price = dict_prices[card][param]
            try:
                res[card] = float(price)
            except (TypeError, ValueError):    # price is None
                print(f"{card} has {price} price!!!")
                errors.append(card)
    
    if fill_errors_by_hand is True:
        for card in tqdm(errors):
            if "eur" in param:
                webbrowser.open("https://www.cardmarket.com/en/Magic/Cards/" + card.replace(" ", "-").replace(
                    ",", "").replace("'", ""))
            elif "usd" in param:
                webbrowser.open("https://www.tcgplayer.com/search/all/product?q=" + card)
                
            hand = input("Insert Price or break to interrupt.")
            if hand.lower() == 'break':
                break
            try:
                res[card] = float(hand)
            except Exception as e:
                print(e)
                print(f"Not valid price inserted. {card} will be skipped")

    with open(file, "w") as jf:
        json.dump(res, jf)
    return res


if __name__ == "__main__":
    path_or_lista = input('Insert a path or a list of cards')
    if path_or_lista[0] == '[':
        cards = json.loads(path_or_lista)    
    else:
        try:
            with open(path_or_lista) as f:
                cards = json.load(f)
        except FileNotFoundError as e:
            cards = path_or_lista
            
    cards = set(cards)
    print("You have", len(cards), "cards.")

    prices = get_scryfall_prices(cards)
    
    eur_file = "new_eur_prices.json"
    usd_file = "new_usd_prices.json"
    decompose(prices, "eur", eur_file, fill_errors_by_hand=True)
    decompose(prices, "usd", usd_file, fill_errors_by_hand=True)
    
    print("Prices saved on", eur_file, "and", usd_file)
