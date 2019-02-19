import threading
from queue import Queue
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

mongo_client = MongoClient('localhost', 27017)
mongo_db = mongo_client['spyshopify']
mongo_docs = mongo_db['shopifysites']


def web_list_divine(web_list, divine_num):
    # divine original list into other list with divine_num index with original content
    num = len(web_list) // divine_num
    total_list = [web_list[i: i + num] for i in range(0, len(web_list), num)]

    if len(total_list) > divine_num:
        for i in range(divine_num + 1, len(total_list)):
            total_list[divine_num] += total_list[i]

    for j in range(len(total_list) - 1, divine_num, -1):
        total_list.remove(total_list[j])

    return total_list


def open_thread(targets, args_set):
    thread = threading.Thread(target=targets,
                              args=args_set)
    thread.start()
    return thread


def get_site_list(file_url):
    with open(file_url, 'r') as f:
        site_list = []
        for line in f:
            line = line.rstrip()
            site_list.append(line)

    return site_list


def site_request_check(site_list):
    for site in site_list:
        try:
            with requests.get(site) as response:
                if response.status_code == 200:
                    print('Getting ' + site)
                    shoptify_check(site, response)
                    # queue1.put(site)  # site are okay
        except:
            pass


def shoptify_check(site, respone):
    script_check = []
    try:
        soup = BeautifulSoup(respone.text, features='html.parser')
        for script in soup.find_all('script', id='shopify-features'):
            script_check.append(script)
            if len(script_check) != 0:
                print('Insert ' + site)
                update_database(site)
    except:
        pass


def update_database(site):
    check = []
    for i in mongo_docs.find({'sites_name': site}):
        check.append(i)
    if len(check) == 0:
        mongo_docs.insert_one({'sites_name': site})


def main(sites):
    threads_list = []
    thread_num = min(200, len(sites))
    divined_sites_list = web_list_divine(sites, thread_num)
    for num_port in range(thread_num + 1):
        thread = open_thread(site_request_check, (divined_sites_list[num_port],))
        threads_list.append(thread)
    # gather opened threads
    for thread in threads_list:
        thread.join()


if __name__ == '__main__':
    siteslist = get_site_list('shopify-sitelist.txt')
    main(siteslist)
