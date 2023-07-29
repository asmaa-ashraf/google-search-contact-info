from googlesearch import search
import requests
import bs4
import phonenumbers
from email_validator import validate_email
import pandas as pd
import certifi
import http.client
import sys
#7:00
results_df = pd.read_csv('results.csv')
print(results_df.keys())
fail_names = pd.DataFrame(columns=['name', 'link'])
headers = {
    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/81.0.4044.141 Safari/537.36"}
timeout = 50


def check_url(url, name):
    # companies url should contain its name
    name=name.replace('-',' ').replace('_',' ').replace('.',' ').replace(',',' ').lower()
    names1=name.split(' ')
    names=[]
    for nam in names1:
        nam="".join(ch for ch in nam if ch.isalnum())
        names.append(nam)
    if name in url:
        name_check = True
    elif all(name in url for name in names):
        name_check = True
    else:
        print('not all '+name+' in url '+url)
        name_check = False
    # companies url must not be a wikipedia a facebook instagram twitter
    webs = ['wikipedia', 'facebook', 'instagram', 'twitter', 'amazon','linkedin','jumia','github']
    if any(w in url.lower() for w in webs):
        return False
    return name_check


def get_contact_page(text):
    spare_urls=[]
    for url in search(text, stop=10, pause=2):
        if check_url(url, text):
            print('good', url)
            spare_urls.append(url)
        else:
            print('bad url', url)
    if spare_urls:
        return spare_urls,True
    url = 'https://google.com/search?q=' + text
    result_url = ''
    # Fetch the URL data using requests.get(url),
    # store it in a variable, request_result.
    request_result = requests.get(url, headers=headers, timeout=timeout)
    print(request_result.status_code)
    # Creating soup from the fetched request
    soup = bs4.BeautifulSoup(request_result.text, "html.parser")
    allData = soup.find_all("h3")

    for i in allData:
        try:
            parent = i.parent.parent.parent.parent.parent
            if ' AD ' in parent.text:
                continue
            urls = parent.find_all("a")
            x = 0
            contact_url = ''
            for u in urls:
                ur = u.get('href')
                url = 'https:' + ur.split('https:')[1].split('&')[0]
            for u in urls:
                x += 1
                ur = u.get('href')
                url = 'https:' + ur.split('https:')[1].split('&')[0]
                if result_url == '':
                    result_url = url
                if not check_url(url, text):
                    print('bad url:', url)
                    continue
                if 'contact-us' in url:
                    contact_url = url
                    result_url = url
                    print('found contact page', url)
                    break
            if contact_url:
                return contact_url,False
        except Exception as e:
            pass
        if contact_url == '':
            return result_url,False

        return result_url,False


def is_phone(phone):
    try:
        number = phonenumbers.parse(phone)
        if phonenumbers.is_possible_number(number):
            return True
    except Exception as e:
        pass
    if len(phone) > 5 and len(phone) < 15:
        phone1 = phone.replace('-', '').replace('(', '').replace(')', '').replace('+', '').replace(' ', '').replace(
            '\n', '').replace('\t', '')
    try:
        int(phone1)
        return True
    except:
        return False
    return False


def containing_phone(phone):
    phones = []
    phone1 = ''
    phone = phone.replace('\n', ' ')
    if len(phone) > 9:
        i = 0
        for ch in phone:
            deci = False
            try:
                int(ch)
                deci = True
            except:
                pass
            seperators = [' ', '-', '.']
            count_sep = {' ': 0, '-': 0, '.': 0}
            if deci or ch == '+' or ch == '(':
                phone1 += ch
            elif phone1 and any(ch == s for s in seperators):
                count_sep[ch] += 1
                if count_sep[ch] < 4:
                    if len(phone)>i+1:
                        if phone[i + 1] in seperators:
                            break
                    phone1 += ch
            elif phone1:
                if is_phone(phone1) and phone1 not in phones:
                    phones.append(phone1)
                else:
                    phone1 = ''
            i += 1

    if is_phone(phone1) and phone1 not in phones:
        phones.append(phone1)
    return phones


def contains_email(word):
    word = word.replace('\n', ' ')
    emails = []
    if '@' not in word:
        return []
    else:
        words = word.split(' ')
        for word in words:
            try:
                if validate_email(word, check_deliverability=False):
                    emails.append(word)
            except:
                pass
        return emails


def get_contact_info(urls,islist):
    if islist:
        url=urls[0]
    else:
        url=urls
    url= contact_page(url)
    soup=''
    print('try url',url)
    try:
        request_result = requests.get(url, timeout=timeout, headers=headers, verify=certifi.where())
        # Creating soup from the fetched request
        soup = bs4.BeautifulSoup(request_result.text, "html.parser")
    except:
        pass

    emails, phones = [], []
    try:
        emails = soup.select('a[href*="mailto"]')
        print(emails)
        emails = []
        for e in emails:
            print('e href', e.get('href'))
            em = e.get('href').replace('mailto:', '')
            et = e.text
            print(em, 'em')
            print(et, 'et')
            emails = contains_email(em)
            if not emails:
                emails = contains_email(et)

    except Exception as e:
        print(e)
    try:
        phones = soup.select('a[href*="tel:"]')
        phone3 = []
        phone = ''
        for p in phones:
            print(p.get('href'), 'ph href')
            ph = p.get('href').replace('tel:', '')
            print('rep ph', ph)
            print(phone, 'phone 1st')
            if not ph:
                ph = p.text
            phones = containing_phone(ph)
    except Exception as e:
        print(e)
    try:
        elements = soup.find('body').findChildren()
        for ele in elements:
            ph = ele.text.lower().replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
            ems = contains_email(ph)
            phs = containing_phone(ph)
            if ems:
                for es in ems:
                    if es not in emails:
                        emails.append(es)
            if phs:
                for ps in phs:
                    if ps not in phones:
                        phones.append(ps)
    except Exception as e:
        print(e)
    if not phones and not emails:
        if islist:
            if len(urls)>2:
                get_contact_info(urls[1:-1],True)

    return phones, emails


def contact_page(url):
    if 'contact' in url.lower():
        return url
    try:
        request_result = requests.get(url, headers=headers, timeout=timeout, verify=certifi.where())
    except:
        return url
    soup = bs4.BeautifulSoup(request_result.text, "html.parser")
    print('getting info from', url)
    link=''
    links = soup.find_all(lambda tag: tag.name == 'a' and tag.get('href') and tag.text)
    for link1 in links:
        if 'contact' in link1.text.lower() and 'contact' in link1['href'].lower():
            print(link1['href'])
            link = link1['href']
    if not link:
        print('not link')
        links = soup.select('a[href*="contact"]')
        try:
            link = links[0].get('href')
        except:
            link = url
    if not link.startswith('http'):
        print(link)
        if url.endswith('/'):
            link1 = url + link
        else:
            link1 = url +'/'+link
        print(link1,'link1')
        request = requests.get(link1)
        if not request.status_code == 200:
            slash = url.split('.')[-1].split('/')[0]+'/'
            link = url.split(slash)[0] + slash + link
            print(link)
        else:
            link = link1

    return link


def action(name, u=''):
    print('action')
    if not u:
        # try:
        result_url ,islist= get_contact_page(name)
        print('resulturl', result_url)
        # except Exception as e:
        #         with open('error.log', 'a') as errorFile:
        #             err ='error in get_contact_page for: '+name+'from:'+result_url+'\nGetting Error:' + str(e) + "\n"
        #             err += '(Thread section) line: ' + str(sys.exc_info()[-1].tb_lineno) + "\n\n"
        #             errorFile.write(err)
    else:
        result_url = u
    if result_url:
        # try:
        phone, email = get_contact_info(result_url,islist)
        results_df.loc[len(results_df)] = [name, result_url, email, phone]
        results_df.to_csv('results.csv',index=False)
    # except Exception as e:
    #       with open('error.log', 'a') as errorFile:
    #           err ='error in get_contact_info for: '+name+'from:'+result_url+'\nGetting Error:' + str(e) + "\n"
    #           err += '(Thread section) line: ' + str(sys.exc_info()[-1].tb_lineno) + "\n\n"
    #           errorFile.write(err)

    if not result_url or not phone or not email:
        fail_names.loc[len(fail_names)] = [name, result_url]
        fail_names.to_csv('fail.csv')


# checking and fixing results
def check_results(results_file):
    results = pd.read_csv(results_file)
    print(len(results))
    for i, result in results.iterrows():
        problem = result.loc['problem']
        name = result.loc['name']
        if name in results_df['Company']:
            continue
        if str(problem) == 'nan':
            action(name)
        elif not problem or 'url' in problem or problem == '':
            action(name)
        else:
            action(name, result('link'))


check_results('new_results.csv')
