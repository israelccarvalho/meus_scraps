import os  # Adicionando a importação do módulo os
import time
import random
import pandas as pd  # Importação do pandas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup  # Para parsear o HTML e extrair o texto

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

    # Configurar o caminho do chromedriver
    service = Service(executable_path="/usr/bin/chromedriver")  # Ajuste o caminho do chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def login(driver, email, senha):
    """
    Realiza o login no site Escavador.
    """
    driver.get("https://www.escavador.com/")
    wait = WebDriverWait(driver, 30)  # Tempo de espera para elementos carregarem

    # Tenta localizar e clicar no link "Entrar"
    try:
        entrar_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Entrar"))
        )
        entrar_link.click()
    except Exception as e:
        print(f"Erro ao clicar em 'Entrar': {e}")
        raise Exception("Erro ao localizar ou clicar em 'Entrar'.")

    # Preenche o e-mail
    try:
        email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
        email_input.send_keys(email)
    except Exception as e:
        print(f"Erro ao preencher e-mail: {e}")
        raise Exception("Erro ao preencher o campo de e-mail.")

    # Preenche a senha
    try:
        senha_input = wait.until(EC.visibility_of_element_located((By.ID, "senha")))
        senha_input.send_keys(senha)
    except Exception as e:
        print(f"Erro ao preencher a senha: {e}")
        raise Exception("Erro ao preencher o campo de senha.")

    # Clica no botão de login
    try:
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="submit-btn"]'))
        )
        login_button.click()
    except Exception as e:
        print(f"Erro ao clicar no botão de login: {e}")
        raise Exception("Erro ao clicar no botão de login.")

    # Aguarda redirecionamento pós-login
    time.sleep(5)


def save_page_content(driver, cpf):
    """
    Salva o conteúdo de texto da página de resultados da pesquisa em um arquivo .txt
    """
    # Obtém o HTML da página
    page_html = driver.page_source

    # Usa o BeautifulSoup para parsear o HTML
    soup = BeautifulSoup(page_html, 'html.parser')

    # Extrai o texto limpo (remover tags HTML)
    page_text = soup.get_text(strip=True)

    # Salva o conteúdo em um arquivo de texto
    output_dir = "resultados"
    os.makedirs(output_dir, exist_ok=True)  # Cria a pasta "resultados" caso não exista
    filepath = os.path.join(output_dir, f"{cpf}.txt")

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(page_text)

    print(f"Conteúdo da página salvo para o CPF {cpf} em {filepath}")



def search_by_cpf(driver, cpf):
    """
    Realiza a busca do CPF no site Escavador após o login e salva o conteúdo da página.
    """
    wait = WebDriverWait(driver, 30)

    # Acessa a página de pesquisa
    driver.get("https://www.escavador.com/pesquisa")  # Ajuste se necessário para a URL de pesquisa correta
    print(f"Acessando página de pesquisa para CPF: {cpf}")

    # Aguarda a página carregar completamente
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Localiza o campo de busca e insere o CPF
    try:
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="q"]'))
        )
        print("Campo de pesquisa encontrado.")

        # Preenche o CPF no campo de pesquisa
        search_input.clear()
        search_input.send_keys(cpf)

        # Aguarda um tempo aleatório antes de enviar o formulário
        time.sleep(random.uniform(1, 2))

        # Envia o formulário (pressiona Enter)
        search_input.send_keys(Keys.RETURN)
        print(f"Pesquisa realizada para CPF: {cpf}")

        # Aguarda o carregamento dos resultados
        time.sleep(random.uniform(3, 5))

        # Salva o conteúdo da página
        save_page_content(driver, cpf)

    except Exception as e:
        print(f"Erro ao realizar a busca para CPF {cpf}: {e}")


def process_cpfs(input_csv):
    """
    Lê CPFs do arquivo CSV e processa cada um utilizando Selenium, salvando o conteúdo em .txt
    """
    driver = configure_driver()

    try:
        # Dados para login
        email = "SEU E-MAIL"
        senha = "SUA SENHA"

        # Realiza login
        login(driver, email, senha)

        # Carrega os CPFs do arquivo CSV
        cpfs = pd.read_csv(input_csv)['CPF']

        # Processa cada CPF
        for cpf in cpfs:
            print(f"Processando CPF: {cpf}")
            search_by_cpf(driver, cpf)
            time.sleep(random.uniform(3, 6))  # Atraso aleatório entre buscas

    finally:
        print("Encerrando o navegador...")
        driver.quit()


# Nome do arquivo CSV com os CPFs
input_csv = "cpfs.csv"
process_cpfs(input_csv)
