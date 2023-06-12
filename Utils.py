import asyncio
import datetime
import json
import os
import shelve
import time

import aiohttp
import requests

from utils import Config
from utils.LogController import LogController


class Utils:
    def __init__(self):
        self.logger = LogController.get_logger()

    async def fetch_one_url(self, session, url, save_path=None):
        async with session.get(url) as response:
            time.sleep(0.01)
            response_text = await response.text()
            if save_path is not None:
                with open(save_path, "wb") as text_file:
                    text_file.write(response_text.encode("UTF-8"))
            return url, response_text

    ### dowloads everything from urls, then returns with response
    def download_urls(self, urls: list, save_as={}):
        loop = asyncio.get_event_loop()
        htmls = loop.run_until_complete(self.download_urls_helper(urls, save_as))
        return htmls

    async def download_urls_helper(self, urls: list, save_as: dict):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                if url in save_as:
                    save_path = save_as[url]
                else:
                    save_path = None
                tasks.append(fetch_one_url(session, url, save_path))
            htmls = await asyncio.gather(*tasks)
            return htmls

    # end DOWNLOAD URLS

    def get_number_of_pages(self):
        with open('auction/0.json', 'rb') as f:
            ah_dict = json.load(f)
            if ah_dict['success']:
                number_of_pages = ah_dict['totalPages']
                return number_of_pages
            else:
                print("number_of_pages error")

    def download_auctions(self):
        global cake_auctions_json_list
        global cake_auction_list
        print("Updating all auctions")
        # print("Deleting old auction files")
        for filename in os.listdir('auction'):
            os.remove('auction/' + filename)

        # print("Downloading page 0")
        r = requests.get('https://api.hypixel.net/skyblock/auctions?key=' + Config.API_KEY + '&page=0')
        with open(r'auction/0.json', 'wb') as f:
            f.write(r.content)
        number_of_pages = self.get_number_of_pages()
        print("Downloading", number_of_pages, "pages")

        if number_of_pages is None:
            print('number_of_pages is None for some reason, downloading 2 pages, so the script does not crash')
            number_of_pages = 2

        urls = []
        save_as = {}
        for page_number in range(1, number_of_pages):
            url = 'https://api.hypixel.net/skyblock/auctions?key=' + Config.API_KEY + '&page=' + str(page_number)
            urls.append(url)
            save_as[url] = r'auction/' + str(page_number) + '.json'

        self.download_urls(urls, save_as)
        print("auctions updated")

    def delete_database(self):
        if os.path.exists('mcnames.db'):
            # rename with timestamp
            os.rename('mcnames.db', f'mcnames_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.db')
            print("mcnames.db deleted")

    def is_player_online(self, mc_name):
        try:
            mc_uuid = self.get_uuid_from_mc_name(mc_name)
        except json.decoder.JSONDecodeError:
            print("is_player_online - name changed, old name:", mc_name)
            return "name_not_found_or_changed"

        url = 'https://api.hypixel.net/player?key=' + Config.API_KEY + '&uuid=' + mc_uuid

        try:
            json_player_stats = requests.get(url=url).json()
        except:
            print('INVALID API RESPONSE - it is not known if', mc_name, 'is online')
            return "hypixel_api_is_down"

        if json_player_stats['success']:
            try:
                if json_player_stats['player']['lastLogin'] > json_player_stats['player']['lastLogout']:
                    return "Online"
                else:
                    return "Offline"
            except KeyError:
                # TODO: check why/when this error appears
                return "you_should_never_see_this_error"
        else:
            print("is_player_online - ERROR")
            return False

    def get_uuid_from_mc_name(self, name):
        url = 'https://api.mojang.com/users/profiles/minecraft/' + name
        return requests.get(url=url).json()['id']

    # api limit 600 per 10 minutes = 1 per sec
    def get_mc_name_from_uuid(self, uuid):
        with shelve.open('mcnames') as mcnames:
            if uuid not in mcnames:
                data = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid).json()
                name = data["name"]
                mcnames[uuid] = name
                print("Fetched name from mojang -", mcnames[uuid])
            # time.sleep(0.1)

            found_name = mcnames[uuid]

            return found_name

    # https://stackoverflow.com/questions/3429510/pythonic-way-to-convert-a-list-of-integers-into-a-string-of-comma-separated-rang


def split_message(msg):
    """
    Split message to multiple messages if it is too long.
    """

    msgs = msg.split('\n')

    # merge adjacent if total length is less than 2000
    merged_msgs = []

    adding_to_index = 0
    for msg in msgs:
        if len(merged_msgs) == 0:
            merged_msgs.append(msg)
            continue

        if len(merged_msgs[adding_to_index]) + len(msg) < 1980:
            merged_msgs[adding_to_index] += '\n' + msg
        else:
            merged_msgs.append(msg)
            adding_to_index += 1

    return merged_msgs


def uuid_add_dashes(uuid):
    return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"


def seconds_to_hours_minutes_seconds(seconds: int):
    if seconds < 0:
        return seconds

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    return f'{h:d}:{m:02d}:{s:02d}'


def k_to_mil(num: int):
    return round(num / 1000, 3)


def list_to_ranges(zones):
    buffer = []

    try:
        st = ed = zones[0]
        for i in zones[1:]:
            delta = i - ed
            if delta == 1:
                ed = i
            elif not (delta == 0):
                buffer.append((st, ed))
                st = ed = i
        else:
            buffer.append((st, ed))
    except IndexError:
        pass

    return ','.join(
        "%d" % st if st == ed else "%d-%d" % (st, ed)
        for st, ed in buffer).replace(",", ", ")


def chunks(lst, n):  # https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
