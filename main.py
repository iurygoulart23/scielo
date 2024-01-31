# IMPORTING LIBRARIES
from bs4 import BeautifulSoup
import requests
import os, os.path, csv
import logging
from nturl2path import url2pathname
import re
from lxml import etree
import time
import pandas as pd


def chamar_crawler_scielo(assunto, linguagem):
  
    # DEFINE VARIABLES
    scielo_dict = dict()
    pages = 0
    link = 0
    page_article = 1
    page_number = 1
    titulo_salvo = assunto.replace('+', '_')
    
    def url(assunto, linguagem):
    
        
      print('Validando link da página...')
        
      # FUNCTION TO PUT YOUR SUBJECT CHOSE AND LANGUAGE
      if (linguagem == 'PT') or (linguagem == 'pt'): #or 'portugues' or 'português' or 'Portugues' or 'Português':
        
        link = f'https://search.scielo.org/?lang=pt&count=15&from={str(page_article)}&output=site&sort=&format=summary&fb=&page={str(page_number)}&q={assunto}'
              
      elif (linguagem == 'EN') or (linguagem == 'en'): #or 'ingles' or 'inglês' or 'Ingles' or 'Inglês' or 'english' or 'English':
        link = f'https://search.scielo.org/?lang=en&count=15&from={str(page_article)}&output=site&sort=&format=summary&fb=&page={str(page_number)}&q={assunto}'
                
      else:
        print('Não consegui localizar o link')
        return
  
      return link
  
    
    def get_n_page(link):
        global pages
        
        # time.sleep(1)
        print('Pegando a quantidade de páginas para a pesquisa...')
        
        # REQUEST CONTENT URL
        html_get = requests.get(link)

        # GETTING CONTENT PAGE
        html_page = html_get.text

        # PARSING THE PAGE, PROCESS AND EXTRACTING INFO
        soup = BeautifulSoup(html_page, 'html.parser')

        # GET NUMBER OF PAGES
        try:
            pages = str(soup.find('input',{'class': 'form-control goto_page'}).text.strip())
            pages = int(re.search(r'\d+', pages).group())

        except:
            print('Não encontrei as paginas para sua pesquisa')
        
        
        return (pages)

      
    def crawler(link):
        global pages
        
        # REQUEST CONTENT URL
        #time.sleep(1,2)
        html_get = requests.get(link)

        # GETTING CONTENT PAGE
        html_page = html_get.text

        # PARSING THE PAGE, PROCESS AND EXTRACTING INFO
        soup = BeautifulSoup(html_page, 'html.parser')

        # GET NUMBER OF PAGES
        try:
            pages = str(soup.find('input',{'class': 'form-control goto_page'}).text.strip())
            pages = int(re.search(r'\d+', pages).group())
      
        except:
            print('Não encontrei resultados para sua pesquisa.')
            return

        # GET APPROXIMATELY NUMBER OF ARTICLES
        articles = pages * 15

        # ENTER AT FIRST DIV IN THE CSS CODE
        div_line =  soup.select_one('div.results')
    
        # ENTER AT SECOND DIV INSIDE THE FIRST DIV
        list1 = []
        for link in div_line.select('div.line a[href]'):
            list1.append(link['href'])

        # CLEAR THE list1 AND DROP DUPLICATES
        links_cleared = list(set([x for x in list1 if x.startswith('http://www.scielo.br/scielo.php?script=sci_arttex')]))

        # CREATE A NEW LIST TO GET KEY VALUE TO FILTER BETTER
        pid_list = []
        for link in links_cleared:
            splited = link.split('-')
            x = splited[1].split('&')
            pid_list.append(x[0])

        # CREATE A DICT TO CONNECT LINK AND KEY
        pid_link = dict(zip(links_cleared, pid_list))

        # FILTER DUPLICATES BY THE KEY
        result = {}
        for key,value in pid_link.items():
            if value not in result.values():
                result[key] = value

        # LINK LIST FILTERED
        link_list = list(result.keys())
  
        return link_list
  
    def pegar_conteudo_pagina(link_list):
        global link
        
        print ('Pegando o conteudo das páginas, aguarde...')
    
        for link in link_list:
            # REQUEST CONTENT URL
            #  time.sleep(1)
            html_get = requests.get(link)

            # GETTING CONTENT PAGE
            html_page = html_get.text

            # PARSING THE PAGE, PROCESS AND EXTRACTING INFO
            soup = BeautifulSoup(html_page, 'html.parser')
      

            # GET TITLE FROM THE ARTICLE
            title = (soup.find('h1',{'class': 'article-title'}).text.strip())

            # GET ABSTRACT FROM ARTICLE
            abstract = (soup.select_one('p', {'class': 'articleSection'}).text.strip())

            # GET KEYWORDS FROM ARTICLE
            dom = etree.HTML(str(soup))
            keywords = (str(dom.xpath('//*[@id="articleText"]/div[1]/p[2]/text()')))

            # GET ARTICLE YEAR
            received_date = (str(dom.xpath('//*[@id="articleText"]/div[7]/div/div/ul/li[1]/text()'))\
                            .replace('\\','/')\
                            .replace("['/n', '", "")\
                            .replace('xa', '')\
                            .replace("']", ''))

            accepted_date = (str(dom.xpath('//*[@id="articleText"]/div[7]/div/div/ul/li[2]/text()'))\
                            .replace('\\','/')\
                            .replace("['/n', '", "")\
                            .replace('xa', '')\
                            .replace("']", ''))

            # GET AUTHORS OF THE ARTICLE
            authors = soup.select_one('div.contribGroup .dropdown a').parent.parent
            authors = [x.strip() for x in authors.text.split('\n') if x.startswith(' ')]
      

            # CREATE A DICT TO PUT ALL THE INFO COLLECTED
            scielo_dict2 = {
                        'titulo': [title], 'resumo': [abstract], 'palavras_chave': [keywords],\
                        'autores': [authors], 'data_recebimento': [received_date],\
                        'data_aceite': [accepted_date], 'link': [link]
                            }
    
    
            # LOOP TO INSERT NEW INFO TO DICT WITHOUT OVERWRITE
            for key, value in scielo_dict2.items():
                if key in scielo_dict:
                    if isinstance(scielo_dict[key], list):
                        scielo_dict[key].append(value)
                    else:
                        temp_list = [scielo_dict[key]]
                        temp_list.append(value)
                        scielo_dict[key] = temp_list
                else:
                    scielo_dict[key] = value
    
    # LOOP TO ITERATE THROW ALL SEARCH PAGES
    pages = get_n_page(url(assunto, linguagem))
    
    # LOOP TO GET PAGE CONTENT AND CHANGE PAGE
    while page_number != pages:
        pegar_conteudo_pagina(crawler(url(assunto, linguagem)))
        page_article = page_article + 15
        page_number = page_number + 1
        #  time.sleep(1)
        print('Trocando de página')
        
    else:
        print('Gerando arquivo com o resultado da pesquisa')
        dict_columns = ['titulo', 'resumo', 'palavras_chave',\
                        'autores', 'data_recebimento',\
                        'data_aceite', 'link']
        try:
          # TRANSFORM DICT TO DF AND TO CSV
          scielo_dict_df = pd.DataFrame.from_dict(scielo_dict)
          scielo_dict_df = pd.DataFrame.to_csv(scielo_dict_df)
          
          # SAVING
          with open('path para salvar seu arquivo'+ titulo_salvo + '_scielo.csv', 'wb') as f:
              f.write(scielo_dict_df.encode())
              f.close()
              print('Arquivo gerado com sucesso.')
        except:
          print('Não foi possivel gerar o arquivo.')
          return
    
    return print('Fim da execução.')