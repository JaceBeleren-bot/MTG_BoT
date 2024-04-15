import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def query_scryfall(query):
    """Perform a fuzzy search for a card by name."""
    response = requests.get(f"https://api.scryfall.com/cards/named?fuzzy={query}")
    return response.json() if response.status_code == 200 else {"error": "Card not found"}

def query_scryfall_with_list(query):
    """Query Scryfall for a list of cards matching the complex search query."""
    encoded_query = requests.utils.quote(query)
    search_url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    response = requests.get(search_url)
    if response.status_code == 200:
        search_results = response.json()
        if search_results['object'] == 'list' and search_results['total_cards'] > 0:
            response_text = "Top matches:\n"
            for card in search_results['data'][:3]:
                response_text += f"{card['name']} - {card.get('mana_cost', 'N/A')}\n"
                response_text += f"Type: {card.get('type_line', 'N/A')}\n"
                response_text += f"Oracle Text: {card.get('oracle_text', 'N/A')[:100]}...\n"
                response_text += f"More Info: {card['scryfall_uri']}\n\n"
            return response_text.strip()
        else:
            return "No matches found."
    else:
        return "Failed to query Scryfall."

def get_card_image(card_name):
    """Fetch the image URL of a card."""
    data = query_scryfall(card_name)
    return data.get('image_uris', {}).get('normal', "Image not found.") if "image_uris" in data else "Card not found."

def get_card_text(card_name):
    """Retrieve the oracle text of a card."""
    data = query_scryfall(card_name)
    return data.get('oracle_text', "Text not found.") if "oracle_text" in data else "Card not found."
#acha as top rullings, nao esta implementada embora a funcao ja esteja pronta
def get_card_rulings(card_name):
    """Get the rulings for a card."""
    card_data = query_scryfall(card_name)
    if "error" not in card_data:
        rulings_uri = card_data.get('rulings_uri')
        rulings_response = requests.get(rulings_uri)
        if rulings_response.status_code == 200:
            rulings_data = rulings_response.json()
            rulings = rulings_data.get('data', [])
            return "\n".join([ruling['comment'] for ruling in rulings[:5]]) if rulings else "No rulings found."
        else:
            return "Failed to fetch rulings."
    return "Card not found."
#acha o preço, funciona bem mas n está implementada
def get_card_price(card_name):
    """Fetch the price (USD and TIX) of a card."""
    data = query_scryfall(card_name)
    if not data:
        return "Card not found."
    usd_price = data.get('prices', {}).get('usd', "USD price not available.")
    tix_price = data.get('prices', {}).get('tix', "TIX price not available.")
    return f"USD: {usd_price}, TIX: {tix_price}"

def send_reply(driver, reply):
    """Send a reply message in the WhatsApp chat."""
    message_input_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//footer//div[@contenteditable='true']"))
    )
    message_input_box.send_keys(reply + Keys.ENTER)

def listen_for_messages(driver, chat_name):
    """Listen for messages in a specified chat and process !mtg commands."""
    search_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
    )
    search_box.send_keys(chat_name)
    time.sleep(2)
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)

    print(f"Listening to messages in {chat_name}...")
    last_read_message = None

    #A classe do chat, achada com webscrapping, pode mudar...
    while True:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//span[contains(@class, 'copyable-text')]"))
            )
            messages = driver.find_elements(By.XPATH, "//span[@dir='ltr']/span")
            if messages:
                latest_message = messages[-1].text
                if latest_message != last_read_message:
                    print(f"New message: {latest_message}")
                    last_read_message = latest_message  # Update last_read_message here
                    
                    # Comando com as informacoes
                    if latest_message == "!mtg help":
                        help_link = "Here's the MTG Bot documentation you requested: https://drive.google.com/file/d/1aQpbR3kLC3l_wA26drgsK54OeR3yoX4M/view?usp=share_link"
                        send_reply(driver, help_link)
                    
                    # Estrutura da query
                    elif latest_message.startswith("!mtg query"):
                        query = latest_message[len("!mtg query"):].strip()
                        response = query_scryfall_with_list(query)
                        send_reply(driver, response)
        except Exception as e:
            print(f"Error reading messages: {e}")
        
        time.sleep(1)  # Intervalo para novas mensagens 

# Inicia o WebDriver e o Whats
driver = webdriver.Chrome()  # Lembre de ter o SEU path do chrome drive
driver.get("https://web.whatsapp.com")
print("Please scan the QR Code and press Enter")
input()
chat_name = "Notas"  # Aqui vai o nome do seu chat, mas voce ainda pode trocar manualmente pelo browser
listen_for_messages(driver, chat_name)
