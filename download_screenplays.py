import os
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd


BASE_URL = 'http://www.imsdb.com'
SCRIPTS_DIR = 'data\\screenplays'
CSV_NAME = "data\\data.csv"

def clean_script(text):
    text = text.replace('Back to IMSDb', '')
    text = text.replace('''<b><!--
</b>if (window!= top)
top.location.href=location.href
<b>// -->
</b>
''', '')
    text = text.replace('''          Scanned by http://freemoviescripts.com
          Formatting by http://simplyscripts.home.att.net
''', '')
    return text.replace(r'\r', '')


def get_script(relative_link):
    tail = relative_link.split('/')[-1]
    print('fetching %s' % tail)
    script_front_url = BASE_URL + quote(relative_link)
    front_page_response = requests.get(script_front_url)
    front_soup = BeautifulSoup(front_page_response.text, "html.parser")

    try:
        script_link = front_soup.find_all('p', align="center")[0].a['href']
    except IndexError:
        print('%s has no script :(' % tail)
        return None, None

    if script_link.endswith('.html'):
        title = script_link.split('/')[-1].split(' Script')[0]
        script_url = BASE_URL + script_link
        script_soup = BeautifulSoup(requests.get(script_url).text, "html.parser")
        script_text = script_soup.find_all('td', {'class': "scrtext"})[0].get_text()
        script_text = clean_script(script_text)
        return title, script_text
    else:
        print('%s is a pdf :(' % tail)
        return None, None


def process_task(paragraph):
    try:
        relative_link = paragraph.a['href']
        title, script = get_script(relative_link)
        if not (script and ('INT' in script or 'EXT' in script)):
            return None

        filename = title.strip('.html') + '.txt'

        with open(os.path.join(SCRIPTS_DIR, filename), 'w', encoding="utf-8") as outfile:
            outfile.write(script)
    
        outfile.close()

        return filename

    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    
    response = requests.get('http://www.imsdb.com/all%20scripts/')
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all('p')

    with Pool(10) as p:
        results = p.map(process_task, paragraphs)
    
    filenames = [x for x in results if x is not None]
    movienames = []

    for filename in filenames:
        if ",-The" in filename:
            filename = "The-" + filename.replace(",-The", "")
        if ",-A" in filename:
            filename = "A-" + filename.replace(",-A", "")

        filename = filename.replace(".txt", "")
        filename = filename.replace("-", " ")

        movienames.append(filename)


    df = pd.DataFrame(list(zip(movienames, filenames)), columns = ['movieName', 'fileΝame'])

    df.to_csv(CSV_NAME, encoding='utf-8', index=False)

    print(sum(x is None for x in results))
