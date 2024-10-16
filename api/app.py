from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    search_keyword = request.form['search']
    num_paginas = int(request.form['num_pages'])
    palavras_chave = request.form['keywords'].split(',')
    palavras_chave = [palavra.strip().lower() for palavra in palavras_chave]
    results = search_linkedin(username, password, search_keyword, num_paginas, palavras_chave)
    return render_template('resultados.html', results=results)

def search_linkedin(username, password, search_keyword, num_paginas, palavras_chave):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    result_data = []

    try:
        login_url = 'https://www.linkedin.com/feed/'
        driver.get(login_url)
        username_input = driver.find_element(By.ID, 'username')
        password_input = driver.find_element(By.ID, 'password')
        login_button = driver.find_element(By.CLASS_NAME, 'btn__primary--large')
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()
        time.sleep(35)

        for page in range(1, num_paginas + 1):
            url_pesquisa = f'https://www.linkedin.com/search/results/people/?keywords={search_keyword}&page={page}'
            driver.get(url_pesquisa)
            time.sleep(5)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            perfis = soup.find_all('a', class_='app-aware-link scale-down')
            hrefs = [perfil['href'] for perfil in perfis if 'href' in perfil.attrs and 'miniProfileUrn' in perfil['href']]

            for href in hrefs:
                driver.get(href)
                time.sleep(5)
                html = driver.page_source
                perfil_data = verificar_palavras_chave_e_ocupacao(html, palavras_chave, href)
                result_data.append(perfil_data)

    finally:
        driver.quit()

    return result_data

def verificar_palavras_chave_e_ocupacao(html, palavras_chave, perfil_link):
    soup = BeautifulSoup(html, 'html.parser')
    name = soup.find('h1', class_='text-heading-xlarge inline t-24 v-align-middle break-words')
    occupation = soup.find('div', class_='text-body-medium break-words')
    sections = soup.find_all('section', class_='artdeco-card pv-profile-card break-words mt2')
    section_collect = [0, 1, 2, 3, 4]
    conteudo_total = ''
    
    if occupation:
        conteudo_total += occupation.get_text(strip=True) + '\n'
    for idx in section_collect:
        section_text = sections[idx].get_text(strip=True)
        conteudo_total += section_text + '\n'

    conteudo_total = conteudo_total.lower()
    palavras_encontradas = 0
    for palavra in palavras_chave:
        padrao_exato = r'\b' + re.escape(palavra) + r'\b'
        if re.search(padrao_exato, conteudo_total):
            palavras_encontradas += 1

    compatibilidade = (palavras_encontradas / len(palavras_chave)) * 100

    return {
        'name': name.get_text(strip=True) if name else 'N/A',
        'link': perfil_link,
        'occupation': occupation.get_text(strip=True) if occupation else 'N/A',
        'compatibility': f"{compatibilidade:.2f}%"
    }

if __name__ == "__main__":
    app.run(debug=True)
