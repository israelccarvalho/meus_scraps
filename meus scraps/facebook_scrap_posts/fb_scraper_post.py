import os
import pickle
import random
import time
from urllib.parse import urlparse
from urllib.request import urlretrieve
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# Caminho do ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"
# Configurar tamanho da janela do navegador
driver.set_window_size(1280, 1024)  # Define um tamanho consistente para evitar problemas

# Configurações do Selenium para evitar detecção de bot
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features")
options.add_argument("--disable-blink-features=AutomationControlled")

# Configuração do ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Função para criar diretórios
def create_directories(base_folder, profile_url):
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

# Função para simular movimentos do mouse humano
def human_like_mouse_movement(driver):
    action = ActionChains(driver)
    for _ in range(random.randint(3, 6)):
        x = random.randint(0, 500)
        y = random.randint(0, 500)
        action.move_by_offset(x, y).perform()
        time.sleep(random.uniform(0.5, 1.5))

# Função de login no Facebook
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

# Carregar cookies para evitar novo login
def load_cookies():
    with open("facebook_cookies.pkl", "rb") as file:
        cookies = pickle.load(file)
    driver.get("https://www.facebook.com")
    time.sleep(2)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

# Função para extrair posts do perfil
def scrape_posts(profile_url, result_folder):
    driver.get(profile_url)
    time.sleep(3)
    posts = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    post_count = 0

    while True:
        # Extrair posts visíveis
        post_elements = driver.find_elements(By.XPATH, "//div[@data-ad-preview='message']")
        for post in post_elements:
            try:
                post_count += 1
                content = post.text
                # Salvar conteúdo de texto
                text_filename = os.path.join(result_folder, f"post_{post_count}_text.txt")
                with open(text_filename, "w", encoding="utf-8") as file:
                    file.write(content)
                print(f"Texto do post salvo: {text_filename}")

                # Extrair fotos (se houver)
                photo_elements = post.find_elements(By.XPATH, ".//img")
                for i, photo in enumerate(photo_elements):
                    photo_url = photo.get_attribute("src")
                    if photo_url:
                        photo_filename = os.path.join(result_folder, f"post_{post_count}_photo_{i + 1}.jpg")
                        urlretrieve(photo_url, photo_filename)
                        print(f"Foto salva: {photo_filename}")

            except Exception as e:
                print(f"Erro ao extrair um post: {e}")

        # Rolagem
        human_like_scroll(driver)
        human_like_mouse_movement(driver)

        # Verificar se há mais conteúdo para carregar
        time.sleep(random.uniform(2, 4))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Não há mais posts para carregar.")
            break
        last_height = new_height

# Função principal
def main():
    email = input("Digite seu email do Facebook: ")
    password = input("Digite sua senha do Facebook: ")
    profile_url = input("Digite a URL do perfil para extração dos posts: ")

    # Login e salvamento de cookies
    login_facebook(email, password)

    # Carregar cookies e iniciar extração
    load_cookies()

    # Criar pasta para resultados
    result_folder = create_directories("resultados", profile_url)

    # Extrair posts e salvar resultados
    scrape_posts(profile_url, result_folder)

    # Fechar o navegador
    driver.quit()

if __name__ == "__main__":
    main()
