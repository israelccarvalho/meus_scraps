import os
import time
import random
import json
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv


def configure_driver():
    """
    Configura o driver Selenium com ajustes para evitar detecção.
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(executable_path="/usr/bin/chromedriver")  # Ajuste o caminho do chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def move_mouse_randomly(driver, duration=2):
    """
    Move o mouse aleatoriamente para simular um comportamento humano.
    """
    actions = webdriver.ActionChains(driver)
    for _ in range(int(duration * 5)):
        actions.move_by_offset(random.randint(-5, 5), random.randint(-5, 5)).perform()
        time.sleep(random.uniform(0.1, 0.3))


def login_instagram(driver, email, password):
    """
    Realiza login no Instagram e salva os cookies de sessão.
    """
    driver.get("https://www.instagram.com/")
    wait = WebDriverWait(driver, 30)

    try:
        # Aguardar a página carregar completamente
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Preenche o e-mail ou nome de usuário
        email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="username"]')))
        email_input.clear()
        email_input.send_keys(email)

        # Preenche a senha
        password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="password"]')))
        password_input.clear()
        password_input.send_keys(password)

        # Submete o formulário
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        login_button.click()

        # Aguarda login
        time.sleep(random.uniform(5, 10))  # Tempo aleatório para parecer humano

        # Salva os cookies de sessão
        cookies = driver.get_cookies()
        with open("cookies.json", "w") as file:
            json.dump(cookies, file)
        print("Cookies salvos com sucesso!")

    except Exception as e:
        print(f"Erro ao realizar login: {e}")
        raise


def fetch_external_ids(driver, latlong_csv):
    """
    Processa latitude e longitude para extrair external_ids e salva no CSV.
    """
    latlong_data = pd.read_csv(latlong_csv)
    external_ids = []

    for _, row in latlong_data.iterrows():
        latitude, longitude = row['latitude'], row['longitude']
        url = f"https://www.instagram.com/location_search/?latitude={latitude}&longitude={longitude}"
        print(f"Acessando URL: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 6))  # Aguarda a resposta carregar

        try:
            # Busca o conteúdo da página (JSON no elemento <pre>)
            response = driver.find_element(By.TAG_NAME, "pre").text
            data = json.loads(response)

            # Verifica e extrai os external_ids de 'venues'
            venues = data.get('venues', [])
            for venue in venues:
                external_id = venue.get('external_id')
                if external_id:
                    external_ids.append(external_id)
                    print(f"Encontrado external_id: {external_id}")

        except Exception as e:
            print(f"Erro ao buscar external_ids para latitude={latitude}, longitude={longitude}: {e}")

    # Salva os external_ids em um arquivo CSV
    output_file = "external_id.csv"
    pd.DataFrame({'external_id': external_ids}).to_csv(output_file, index=False)
    print(f"External_ids salvos em {output_file}")


def scroll_to_end(driver):
    """
    Rola a página até o final com intervalos de tempo aleatórios.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Rola até o final da página
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 5))  # Aguarda um tempo aleatório
        
        # Verifica se a altura da página não mudou (fim da página)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Fim da página alcançado.")
            break
        last_height = new_height


def download_images_with_scroll(driver, external_id):
    """
    Baixa todas as imagens de uma página, rolando até o final de forma incremental.
    Salva as imagens em uma pasta nomeada com o external_id, evitando duplicações.
    """
    # Caminho da pasta para salvar as imagens
    output_dir = os.path.join("images", str(external_id))
    
    # Verifica se a pasta já existe
    if os.path.exists(output_dir):
        update = input(f"A pasta para o external_id {external_id} já existe. Deseja atualizá-la? (s/n): ").strip().lower()
        if update != "s":
            print(f"Pulando external_id {external_id}.")
            return
    else:
        os.makedirs(output_dir, exist_ok=True)

    # Conjunto para armazenar URLs de imagens já baixadas
    downloaded_urls = set()
    existing_files = {file for file in os.listdir(output_dir) if file.endswith(".jpg")}
    for file_name in existing_files:
        downloaded_urls.add(file_name.split("_")[-1].split(".")[0])

    print(f"Começando a coleta para external_id {external_id}...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Coleta imagens na página atual
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            src = img.get_attribute("src")
            if src and src not in downloaded_urls:
                try:
                    # Extrai o nome da imagem a partir da URL (parte após o último '/')
                    img_name = src.split("/")[-1].split("?")[0]  # Extrai o nome da imagem
                    img_path = os.path.join(output_dir, img_name)
                    if not os.path.exists(img_path):
                        response = requests.get(src)
                        response.raise_for_status()
                        with open(img_path, "wb") as file:
                            file.write(response.content)
                        downloaded_urls.add(src)
                        print(f"Imagem salva: {img_path}")
                    else:
                        print(f"Imagem {img_name} já existe, ignorando.")
                except Exception as e:
                    print(f"Erro ao baixar imagem de {src}: {e}")

        # Rola a página para carregar mais conteúdo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(8, 15))  # Aguarda mais tempo para as imagens carregarem

        # Verifica se a página não mudou mais
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Fim da página alcançado. Não há mais conteúdo para carregar.")
            break
        last_height = new_height

        # Aguarda o carregamento da nova parte da página (aguarda mais alguns segundos)
        time.sleep(random.uniform(8, 15))  # Tempo adicional para simular espera humana


def navigate_and_download_images(driver):
    """
    Navega para as URLs usando os external_ids e baixa as imagens com scroll down incremental.
    """
    external_ids = pd.read_csv("external_id.csv")['external_id']

    for external_id in external_ids:
        url = f"https://www.instagram.com/explore/locations/{external_id}/"
        print(f"Navegando para {url}")
        driver.get(url)
        time.sleep(random.uniform(8, 20))  # Aguarda a página carregar
        
        # Chama a função para baixar imagens com scroll incremental
        download_images_with_scroll(driver, external_id)


def main():
    driver = configure_driver()

    try:
        # Solicita email e senha ao usuário
        email = input("Digite o e-mail: ")
        password = input("Digite a senha: ")

        # Realiza login no Instagram
        login_instagram(driver, email, password)

        # Processa latitudes e longitudes
        latlong_csv = "latlong.csv"
        fetch_external_ids(driver, latlong_csv)

        # Navega para os locais encontrados e baixa imagens
        navigate_and_download_images(driver)

    finally:
        print("Encerrando o navegador...")
        driver.quit()


if __name__ == "__main__":
    main()
