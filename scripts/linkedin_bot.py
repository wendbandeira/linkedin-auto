import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

def login_to_linkedin(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    username = driver.find_element(By.NAME, "session_key")
    password_input = driver.find_element(By.NAME, "session_password")
    username.send_keys(email)
    password_input.send_keys(password)
    login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')
    login_button.click()
    time.sleep(5)

def start_search(driver):
    # Navegar para a página inicial do LinkedIn
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(5)
    
    # Pesquisar perfis e aplicar o filtro de "Pessoas"
    search_box = driver.find_element(By.XPATH, '//input[@aria-label="Pesquisar"]')
    search_box.clear()
    search_box.send_keys('agronegócio')
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    people_filter = driver.find_element(By.XPATH, '//button[text()="Pessoas"]')
    people_filter.click()
    time.sleep(5)

def get_total_profiles_on_page(driver):
    profiles = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
    profile_urls = [profile.get_attribute('href') for profile in profiles]
    print(f"Encontrados {len(profiles)} perfis na página atual.")
    return profile_urls

def go_to_next_page(driver, retry=2):
    attempt = 0
    while attempt < retry:
        try:
            # Realizar o scroll down até o final da página
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Espera breve para garantir que o scroll foi completado
            
            # Espera explícita para garantir que o botão esteja presente
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Avançar" and not(@disabled)]'))
            )

            # Verifica se o botão existe e está habilitado
            if next_button:
                next_button.click()
                print("Avançando para a próxima página...")
                time.sleep(5)  # Espera a página carregar completamente
                return True
            else:
                print("Botão 'Avançar' não está disponível ou está desabilitado.")
                return False
        except Exception as e:
            print(f"Erro ao tentar ir para a próxima página: {e}")
            attempt += 1
            if attempt < retry:
                print("Tentando novamente...")
                time.sleep(5)
            else:
                print("Máximo de tentativas atingido. Recomeçando a partir da pesquisa.")
                start_search(driver)  # Recomeça a partir da pesquisa
                return False

def collect_and_visit_profiles(driver, csv_writer, visited_profiles):
    while True:
        profile_urls = get_total_profiles_on_page(driver)
        
        for profile_url in profile_urls:
            if profile_url not in visited_profiles:
                # Abrir o perfil em uma nova aba
                driver.execute_script("window.open(arguments[0]);", profile_url)
                driver.switch_to.window(driver.window_handles[-1])
                
                # Esperar a página carregar e realizar a visita
                time.sleep(5)
                csv_writer.writerow([profile_url])
                print(f"Visitando perfil: {profile_url}")
                time.sleep(20)  # Espera de 20 segundos entre as interações com os perfis
                
                # Fechar a aba e voltar para a aba principal
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
                visited_profiles.add(profile_url)
            else:
                print(f"Perfil já visitado: {profile_url}")

        if not go_to_next_page(driver):
            break

def main():
    # Configurar o WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # Fazer login no LinkedIn
    login_to_linkedin(driver, 'email', 'password')
    
    # Verificar se o diretório data/ existe, se não, criar
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Carregar URLs já visitados
    visited_profiles = set()
    if os.path.exists('data/profiles_visited.csv'):
        with open('data/profiles_visited.csv', mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                visited_profiles.add(row[0])
    
    # Realizar a pesquisa inicial
    start_search(driver)
    
    # Abrir o arquivo CSV para escrita
    with open('data/profiles_visited.csv', mode='a', newline='') as file:
        csv_writer = csv.writer(file)
        
        # Escrever cabeçalho se o arquivo estiver vazio
        if file.tell() == 0:
            csv_writer.writerow(['Profile URL'])
        
        # Coletar e visitar perfis
        collect_and_visit_profiles(driver, csv_writer, visited_profiles)
    
    driver.quit()

if __name__ == "__main__":
    main()
