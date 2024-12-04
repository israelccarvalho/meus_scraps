import os
import pickle
import random
import time
import requests
import json
import re
from urllib.parse import urlparse
from urllib.request import urlretrieve
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException

# Caminho do ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"

# Configurações do Selenium para evitar detecção de bot
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features")
options.add_argument("--disable-blink-features=AutomationControlled")

# Configuração do ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Função para verificar conexão com a internet
def wait_for_internet_connection(retry_interval=5):
    print("Verificando conexão com a internet...")
    while True:
        try:
            requests.get("https://www.google.com", timeout=5)
            print("Conexão com a internet restabelecida.")
            return
        except requests.ConnectionError:
            print(f"Sem conexão. Tentando novamente em {retry_interval} segundos...")
            time.sleep(retry_interval)

# Função para criar diretórios
def create_or_check_directory(base_folder, profile_url):
    parsed_url = urlparse(profile_url)
    folder_name = parsed_url.netloc + parsed_url.path.replace('/', '_')
    result_folder = os.path.join(base_folder, folder_name)
    os.makedirs(result_folder, exist_ok=True)
    return result_folder

# Função para simular movimentos de rolagem humano
def human_like_scroll(driver):
    for _ in range(random.randint(2, 5)):
        driver.execute_script("window.scrollBy(0, arguments[0]);", random.randint(300, 600))
        time.sleep(random.uniform(1, 3))

# Função para login no Facebook
def login_facebook(email, password):
    driver.get("https://www.facebook.com")
    time.sleep(2)

    # Inserir email
    email_input = driver.find_element(By.ID, "email")
    email_input.send_keys(email)

    # Inserir senha
    password_input = driver.find_element(By.ID, "pass")
    password_input.send_keys(password)

    # Clicar no botão de login
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()
    time.sleep(5)

    # Salvar cookies
    with open("facebook_cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies salvos com sucesso!")

# Função para carregar cookies
def load_cookies():
    print("Tentando carregar cookies salvos...")
    try:
        with open("facebook_cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
        driver.get("https://www.facebook.com")
        time.sleep(2)
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(5)

        # Verificar se o login foi bem-sucedido
        if "login" in driver.current_url:
            print("Sessão expirada. Realizando login novamente.")
            return False
        print("Sessão restaurada com cookies.")
        return True
    except FileNotFoundError:
        print("Arquivo de cookies não encontrado.")
        return False

# Função para coletar URLs de postagens
def collect_post_urls(profile_url):
    driver.get(profile_url)
    time.sleep(3)
    post_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    consecutive_scroll_attempts = 0  # Contador para tentativas consecutivas de rolagem sem novas URLs
    max_consecutive_attempts = 5    # Limite de tentativas consecutivas sem progresso

    while True:
        # Localizar divs principais
        div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'x9f619 x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6')]")
        new_urls_found = False  # Flag para verificar se novos URLs foram encontrados nesta rolagem

        for div in div_elements:
            try:
                # Dentro de cada div, localizar o elemento <a> com a classe específica
                link_elements = div.find_elements(By.XPATH, ".//a[contains(@href, 'photo.php')]")
                for link in link_elements:
                    href = link.get_attribute("href")
                    if href and href.startswith("https://www.facebook.com/photo.php") and href not in post_urls:
                        post_urls.add(href)
                        new_urls_found = True
                        print(f"URL coletada: {href}")
            except Exception as e:
                print(f"Erro ao processar uma div: {e}")

        # Verificar se novos URLs foram encontrados
        if new_urls_found:
            consecutive_scroll_attempts = 0  # Reinicia o contador se progresso foi feito
        else:
            consecutive_scroll_attempts += 1
            if consecutive_scroll_attempts >= max_consecutive_attempts:
                print("Nenhum novo conteúdo encontrado após múltiplas tentativas. Parando rolagem.")
                break

        # Rolagem
        human_like_scroll(driver)

        # Verificar se há mais conteúdo para carregar
        time.sleep(random.uniform(2, 4))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Não há mais conteúdo para carregar.")
            break
        last_height = new_height

    return list(post_urls)

# Função para salvar imagens de uma URL
def save_images_from_div(url, result_folder):
    driver.get(url)
    time.sleep(3)

    # Filtrar imagens na div específica
    div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'x6s0dn4 x78zum5 xdt5ytf xl56j7k x1n2onr6')]")
    if not div_elements:
        print(f"Nenhuma imagem encontrada em: {url}")
        return None  # Retorna None para indicar que não encontrou nenhuma imagem

    img_paths = []  # Lista para armazenar os caminhos das imagens salvas
    for div in div_elements:
        img_elements = div.find_elements(By.TAG_NAME, "img")
        for img in img_elements:
            img_url = img.get_attribute("src")
            if img_url:
                img_name = os.path.basename(urlparse(img_url).path)
                img_path = os.path.join(result_folder, img_name)

                if not os.path.exists(img_path):
                    urlretrieve(img_url, img_path)
                    print(f"Imagem salva: {img_path}")
                    img_paths.append(img_path)
                else:
                    print(f"Imagem já existe: {img_path}")
                    img_paths.append(img_path)

    return img_paths  # Retorna a lista de caminhos das imagens

# Função para salvar textos em JSON
def save_texts_to_json(url, result_folder, img_paths):
    driver.get(url)
    time.sleep(3)
    all_texts = []

    while True:
        try:
            # Coletar elementos de texto
            text_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'html-div')]//span")
            for text_element in text_elements:
                try:
                    text = text_element.text.strip()
                    if text and text not in all_texts:
                        all_texts.append(text)
                except StaleElementReferenceException:
                    print("Elemento obsoleto. Ignorando e continuando.")
                    continue

            # Tentar clicar no botão "Carregar mais comentários"
            if not click_load_more_button():
                break
        except Exception as e:
            print(f"Erro inesperado ao processar os textos: {e}")
            break

    # Para cada imagem salva, crie um arquivo JSON com o mesmo nome
    if all_texts and img_paths:
        for img_path in img_paths:
            base_name = os.path.splitext(os.path.basename(img_path))[0]  # Remove a extensão da imagem
            json_filename = os.path.join(result_folder, f"{base_name}.json")

            with open(json_filename, "w", encoding="utf-8") as file:
                json.dump(all_texts, file, ensure_ascii=False, indent=4)
            print(f"Texto salvo em: {json_filename}")
    else:
        print(f"Nenhum conteúdo de texto encontrado para salvar em: {url}")

# Função para clicar em "Carregar mais comentários"
def click_load_more_button():
    try:
        button = driver.find_element(By.XPATH, "//div[contains(@class, 'html-div') and @role='button']")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(1)
        button.click()
        time.sleep(random.uniform(2, 4))
        return True
    except (NoSuchElementException, ElementNotInteractableException):
        return False

# Função para criar um nome de arquivo baseado na URL
def create_unique_filename(base_folder, profile_url):
    parsed_url = urlparse(profile_url)
    base_name = f"{parsed_url.netloc.replace('.', '_')}{parsed_url.path.replace('/', '_')}"
    return os.path.join(base_folder, base_name + ".json")

# Função para processar cada URL
def process_url(url, result_folder):
    img_paths = save_images_from_div(url, result_folder)
    if img_paths:
        save_texts_to_json(url, result_folder, img_paths)

# Função principal
def main():
    email = input("Digite seu email do Facebook: ")
    password = input("Digite sua senha do Facebook: ")
    profile_url = input("Digite a URL do perfil para processar: ")

    wait_for_internet_connection()

    if not load_cookies():
        login_facebook(email, password)

    result_folder = create_or_check_directory("resultados", profile_url)
    post_urls = collect_post_urls(profile_url)
    print(f"Total de URLs coletadas: {len(post_urls)}")

    for url in post_urls:
        process_url(url, result_folder)

    driver.quit()

if __name__ == "__main__":
    main()
