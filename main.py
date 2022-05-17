from pprint import pprint

import discord
from discord.ext import commands

import requests
import json

import nbt  # pip3 install NBT
import io
import base64
import zlib
import re
import itertools

import os
import requests
import json
import asyncio
import nest_asyncio
import aiohttp
import time

import shelve

nest_asyncio.apply()


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


import configparser
configParser = configparser.RawConfigParser()
configFilePath = r'config.ini'
configParser.read(configFilePath)

API_KEY = configParser.get('hypixel', 'api_key')
DISCORD_API_KEY = configParser.get('discord', 'api_key')
MAX_CAKE_YEAR = configParser.getint('hypixel', 'max_cake_year')
SLADA_UUID = "ec8d8033fbd148419817dc29227ed555" # TEST UUID

ALLOWED_CHANNEL_IDS = json.loads(configParser.get("discord","allowed_channel_ids"))

COMMAND_PREFIX = configParser.get('discord', 'command_prefix')

if len(ALLOWED_CHANNEL_IDS) == 0:
	print("No allowed channel IDs found in config.ini")
	exit()


# verify if API_KEY is valid
def verify_api_key():
	r = requests.get('https://api.hypixel.net/player?key=' + API_KEY + '&uuid=' + SLADA_UUID)
	if r.status_code == 200:
		return True
	else:
		return False


if not verify_api_key():
	print("Invalid hypixel api_key")
	exit()
else:
	print("Hypixel api_key is valid")



def get_commit_hash():
	return os.popen('git rev-parse --short HEAD').read().strip()

def get_commit_time():
	return os.popen('git show -s --format="%ci"').read().strip()

def get_commit_index():
	count = 100 + int(os.popen('git rev-list --count HEAD').read().strip())
	if git_unsaved_changes():
		return count + 1
	return count

def git_unsaved_changes():
	return len(os.popen('git diff-files').read().strip()) > 0

def git_are_changes_ready_to_commit():
	return os.system('git diff-index --quiet HEAD --') == 0

if git_unsaved_changes():
	BETA = " BETA"
else:
	BETA = ""
VERSION_STRING = f"Bot version{BETA} {get_commit_index()} ({get_commit_hash()}, {get_commit_time()})"

print(VERSION_STRING)

# def get_commit_date():
# 	return get_commit_time().split(' ')[0]

# make dir "auction" if not exists
if not os.path.exists('auction'):
	os.makedirs('auction')


def seconds_to_hours_minutes_seconds(seconds: int):
	if seconds < 0:
		return seconds

	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)

	return f'{h:d}:{m:02d}:{s:02d}'


def uuid_add_dashes(uuid):
	return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"


class TablePrint:
	def __init__(self, widths: tuple):
		self.widths = widths

	def print_row(self, row):
		counter = 0
		ret_str = ""
		for column in row:
			width_correction = 0
			uncolored_string = str(column)

			width_correction = max(0, len(str(column)) - len(uncolored_string))
			ret_str += str(column).ljust(self.widths[counter] + width_correction)
			counter += 1
		ret_str += "\n"
		return ret_str


async def fetch_one_url(session, url, save_path=None):
	async with session.get(url) as response:
		time.sleep(0.01)
		response_text = await response.text()
		if save_path is not None:
			with open(save_path, "wb") as text_file:
				text_file.write(response_text.encode("UTF-8"))
		return url, response_text


# dowloads everything from urls, then returns with response
def download_urls(urls: list, save_as={}):
	loop = asyncio.get_event_loop()
	htmls = loop.run_until_complete(download_urls_helper(urls, save_as))
	return htmls


async def download_urls_helper(urls: list, save_as: dict):
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

def get_number_of_pages():
	with open('auction/0.json', 'rb') as f:
		ah_dict = json.load(f)
		if ah_dict['success']:
			number_of_pages = ah_dict['totalPages']
			return number_of_pages
		else:
			print("number_of_pages error")


def download_auctions():
	global cake_auctions_json_list
	global cake_auction_list
	print("Updating all auctions")
	# print("Deleting old auction files")
	for filename in os.listdir('auction'):
		os.remove('auction/' + filename)

	# print("Downloading page 0")
	r = requests.get('https://api.hypixel.net/skyblock/auctions?key=' + API_KEY + '&page=0')
	with open(r'auction/0.json', 'wb') as f:
		f.write(r.content)
	number_of_pages = get_number_of_pages()
	print("Downloading", number_of_pages, "pages")

	if number_of_pages is None:
		print('number_of_pages is None for some reason, downloading 2 pages, so the script does not crash')
		number_of_pages = 2

	urls = []
	save_as = {}
	for page_number in range(1, number_of_pages):
		url = 'https://api.hypixel.net/skyblock/auctions?key=' + API_KEY + '&page=' + str(page_number)
		urls.append(url)
		save_as[url] = r'auction/' + str(page_number) + '.json'

	download_urls(urls, save_as)
	print("auctions updated")


def get_uuid_from_mc_name(name):
	url = 'https://api.mojang.com/users/profiles/minecraft/' + name
	return requests.get(url=url).json()['id']


# api limit 600 per 10 minutes = 1 per sec
def get_mc_name_from_uuid(uuid):
	with shelve.open('mcnames') as mcnames:
		if uuid not in mcnames:
			url = 'https://api.mojang.com/user/profiles/' + uuid + '/names'

			json_name = requests.get(url=url).json()
			mcnames[uuid] = json_name[-1]['name']
			print("Fetched name from mojang -", mcnames[uuid])
		# time.sleep(0.1)

		found_name = mcnames[uuid]

		return found_name


def k_to_mil(num: int):
	return round(num / 1000, 3)


def is_player_online(mc_name):

	try:
		mc_uuid = get_uuid_from_mc_name(mc_name)
	except json.decoder.JSONDecodeError:
		print("is_player_online - name changed, old name:", mc_name)
		return "name_not_found_or_changed"

	url = 'https://api.hypixel.net/player?key=' + API_KEY + '&uuid=' + mc_uuid

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
			return "you_should_never_see_this_error"
	else:
		print("is_player_online - ERROR")
		return False


# https://stackoverflow.com/questions/3429510/pythonic-way-to-convert-a-list-of-integers-into-a-string-of-comma-separated-rang
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


class InventoryImporter:

	# count_needed = 5
	# order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 69, 70, 71]

	def decode_inventory_data_base64(self, raw_data):
		data = nbt.nbt.NBTFile(fileobj=io.BytesIO(base64.b64decode(raw_data)))
		# print(data.pretty_tree())
		return data

	def decode_inventory_data_raw(self, raw_data):
		data = nbt.nbt.NBTFile(fileobj=io.BytesIO(raw_data))
		return data

	def get_year_of_cake(self, item_in_cake_bag):
		if 'tag' in item_in_cake_bag:
			cake_description = str(item_in_cake_bag['tag']['display']['Lore'])
			reg = re.search(r'the (\d+)(?:st|nd|rd|th)', cake_description)
			if reg:
				cake_year = int(reg.group(1).replace(",", ""))
				return cake_year

			else:
				print("year error", cake_description)

	def list_of_all_items_in_inventories(self, inventories: list):
		all_items = []
		item_storages = []

		for inventory in inventories:
			item_storages.append(self.decode_inventory_data_base64(inventory))

			while len(item_storages) != 0:
				item_storage = item_storages.pop()

				for item in item_storage['i']:
					if 'tag' in item:
						if 'ExtraAttributes' in item['tag']:
							if 'id' in item['tag']['ExtraAttributes']:
								item_type = str(item['tag']['ExtraAttributes']['id'])

								if 'ExtraAttributes' in item["tag"]:
									# print(item["tag"]["ExtraAttributes"])
									if 'new_year_cake_bag_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["new_year_cake_bag_data"].value))
									elif 'greater_backpack_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["greater_backpack_data"].value))
									elif 'jumbo_backpack_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["jumbo_backpack_data"].value))
									elif 'large_backpack_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["large_backpack_data"].value))
									elif 'medium_backpack_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["medium_backpack_data"].value))
									elif 'small_backpack_data' in item["tag"]["ExtraAttributes"]:
										item_storages.append(self.decode_inventory_data_raw(
											item["tag"]["ExtraAttributes"]["small_backpack_data"].value))
									else:
										all_items.append(item)
								else:
									all_items.append(item)
							else:
								all_items.append(item)
						else:
							all_items.append(item)
		return all_items

	def find_cakes_in_item_list(self, item_list: list):
		cake_list = []
		for item in item_list:
			if 'ExtraAttributes' in item["tag"]:
				if 'id' in item['tag']['ExtraAttributes']:
					item_type = str(item['tag']['ExtraAttributes']['id'])
					if item_type == 'NEW_YEAR_CAKE':
						cake_list.append(self.get_year_of_cake(item))
		return cake_list

	def get_pie_info(self, pie_item_extra_attributes):
		try:
			pie_info = {'player': str(pie_item_extra_attributes['leaderboard_player']),
						'position': str(pie_item_extra_attributes['leaderboard_position']),
						'score': str(pie_item_extra_attributes['leaderboard_score']),
						'year': str(pie_item_extra_attributes['event']).replace('spooky_festival_', '').replace('unanticipated_', 'e')}
			if '§c' in pie_info['player']:
				pie_info['rank'] = 'yt/admin'
				pie_info['player'] = pie_info['player'].replace('§c', '')
			elif '§a' in pie_info['player']:
				pie_info['rank'] = 'vip'
				pie_info['player'] = pie_info['player'].replace('§a', '')
			elif '§b' in pie_info['player']:
				pie_info['rank'] = 'mvp'
				pie_info['player'] = pie_info['player'].replace('§b', '')
			elif '§2' in pie_info['player']:
				pie_info['rank'] = 'mod'
				pie_info['player'] = pie_info['player'].replace('§2', '')
			elif '§6' in pie_info['player']:
				pie_info['rank'] = 'mvp++'
				pie_info['player'] = pie_info['player'].replace('§6', '')
			elif '§9' in pie_info['player']:
				pie_info['rank'] = 'helper'
				pie_info['player'] = pie_info['player'].replace('§9', '')
			elif '§7' in pie_info['player']:
				pie_info['rank'] = 'norank'
				pie_info['player'] = pie_info['player'].replace('§7', '')
			else:
				pie_info['rank'] = 'unknown_rank'

			if 'e' not in pie_info['year']:
				pie_info['year'] = str(int(pie_info['year']) + 1)  # fix off by one error
			return pie_info

		except Exception as e:
			print(e, "pie_item_extra_attributes weird", pie_item_extra_attributes)
			return None



	# one pie ExtraAttributes: {TAG_Int('leaderboard_score'): 2858, TAG_String('leaderboard_player'): §cBloozing, TAG_Int('leaderboard_position'): 281, TAG_Int('new_years_cake'): 101, TAG_String('originTag'): EVENT_REWARD, TAG_String('id'): SPOOKY_PIE, TAG_String('event'): spooky_festival_83, TAG_String('uuid'): ccc5d8d2-b9dc-45c5-81bb-9f13d3047249, TAG_String('timestamp'): 11/17/20 7:41 PM}
	def find_pies_in_item_list(self, item_list: list):
		pie_list = []
		for item in item_list:
			if 'ExtraAttributes' in item["tag"]:
				if 'id' in item['tag']['ExtraAttributes']:
					item_type = str(item['tag']['ExtraAttributes']['id'])
					# print(item_type)
					if item_type == 'SPOOKY_PIE':
						pie_info = self.get_pie_info(item['tag']['ExtraAttributes'])
						if pie_info is not None:
							pie_list.append(pie_info)

		# pprint(pie_list)
		return pie_list

	def get_stats(self, personal_profile, profile):
		stats = {}
		current_profile = profile['cute_name']
		stats['current_profile'] = current_profile

		current_profile_uuid = profile['profile_id']
		stats['current_profile_uuid'] = current_profile_uuid

		if 'cute_name' in profile:
			stats['cute_name'] = profile['cute_name']
		else:
			print("CUTE_NAME NOT FOUND", profile)

		if "coin_purse" in personal_profile:
			stats['purse'] = personal_profile['coin_purse']

		if 'auctions_bought_special' in personal_profile['stats']:
			stats['auctions_bought_special'] = personal_profile['stats']['auctions_bought_special']

		if 'auctions_sold_special' in personal_profile['stats']:
			stats['auctions_sold_special'] = personal_profile['stats']['auctions_sold_special']

		if 'auctions_bids' in personal_profile['stats']:
			stats['auctions_bids'] = personal_profile['stats']['auctions_bids']

		return stats

	def get_current_skyblock_profile_uuid(self, uuid: str):
		data = requests.get(
			"https://api.hypixel.net/skyblock/profiles?key=" + API_KEY + "&uuid=" + uuid).json()

		last_save = 0

		if 'profiles' in data:
			for profile in data['profiles']:
				personal_profile = profile['members'][uuid]
				# print("PROF", personal_profile)
				# print(profile['cute_name'], personal_profile['last_save'])
				if 'last_save' in personal_profile:
					if last_save < personal_profile['last_save']:
						last_save = personal_profile['last_save']
						stats = self.get_stats(personal_profile, profile)
					# print("found profile", stats['cute_name'])
					else:
						pass
					# print("skipped profile")
				else:
					print("LAST SAVE NOT IN personal_profile")
		else:
			print('PROFILES NOT FOUND')
			stats = {}
		# profile = data['profile']
		# personal_profile = data['profile']['members'][uuid]
		# stats = self.get_stats(data['profile'], profile)

		return stats

	#
	# 	# print(current_profile, current_profile_uuid)

	def get_profile_details(self, mc_uuid: str, profile_uuid: str, ret_str=""):
		global MAX_CAKE_YEAR

		ret_str += "\nInventory:\n"
		data = requests.get('https://api.hypixel.net/skyblock/profile?key=' + API_KEY + '&profile=' + profile_uuid).json()
		current_member = data['profile']['members'][mc_uuid]

		inventories = []
		# print("\n\n\nget_profile_details current_member:", current_member, "\n\n\n")
		if 'talisman_bag' in current_member:
			inventories = [current_member['talisman_bag']['data'], current_member['ender_chest_contents']['data'],
						   current_member['inv_contents']['data']]
		if 'backpack_contents' in current_member:
			for storage_index in range(19):
				if str(storage_index) in current_member['backpack_contents']:
					if 'data' in current_member['backpack_contents'][str(storage_index)]:
						inventories.append(current_member['backpack_contents'][str(storage_index)]['data'])

		if 'personal_vault_contents' in current_member:
			if 'data' in current_member['personal_vault_contents']:
				inventories.append(current_member['personal_vault_contents']['data'])

		elif 'ender_chest_contents' in current_member:
			ret_str += "Talisman bag not unlocked"
			return ret_str
		else:
			ret_str += "This player does not have his inventory api enabled"
			return ret_str

		cake_list = self.find_cakes_in_item_list(self.list_of_all_items_in_inventories(inventories))
		pie_list = self.find_pies_in_item_list(self.list_of_all_items_in_inventories(inventories))

		# if len(cake_list) == 0:
		# 	print("No cake was found in the inventory. Please enable api access (/sbmenu -> settings -> API settings -> API: inventory - click to enable). After turning on api, go to hub and visit me again please")
		# 	return

		cake_set = set(cake_list)
		# print("Found cakes verbose", sorted(list(cake_set)))

		ret_str += f"Found in inventory: {list_to_ranges(sorted(list(cake_set)))}\n"

		not_owned_cakes = set()

		for i in range(0, MAX_CAKE_YEAR):
			if i not in cake_set:
				not_owned_cakes.add(i)

		ret_str += f"Not found in inventory: {list_to_ranges(sorted(list(not_owned_cakes)))}\n"
		count_needed = 54 - len(cake_set)
		ret_str += f"Needed cakes to complete the bag: {count_needed}\n"

		ret_str += "\nSpooky pies:\n```\n"
		if len(pie_list) == 0:
			ret_str += "No spooky pies found"
		else:
			table = TablePrint((17, 10, 4, 6, 6))
			ret_str += table.print_row(["Name", "rank", "year", "position", "score"])
			for pie in pie_list:
				ret_str += table.print_row([pie['player'], pie['rank'], pie['year'], pie['position'] if (pie['position'] != "-1") else '?', pie['score'] if (pie['score'] != "-1") else '?'])
		ret_str += "```"

		return ret_str

	def offer_cakes(self, mc_name):
		self.mc_name = mc_name

		ret_str = ""

		try:
			mc_uuid = get_uuid_from_mc_name(self.mc_name)
			stats = self.get_current_skyblock_profile_uuid(mc_uuid)

			print("stats:" + str(stats))

			if 'current_profile' in stats:
				ret_str += f"{mc_name} ({stats['current_profile']}) - {is_player_online(mc_name)}:\n"
			else:
				ret_str += f"{mc_name}:\n"

			if 'purse' in stats and stats['purse'] is not None:
				ret_str += f"Purse: {k_to_mil(int(stats['purse']) / 1000)} mil\n"

			ret_str += f"\nAH:\n"

			if 'auctions_bids' in stats:
				ret_str += f"Bids: {int(stats['auctions_bids'])}\n"

			if 'auctions_sold_special' not in stats:
				stats['auctions_sold_special'] = 0

			if 'auctions_bought_special' not in stats:
				stats['auctions_bought_special'] = 0

			ret_str += f"Special bought/sold: {int(stats['auctions_bought_special'])}/{int(stats['auctions_sold_special'])}\n"

			# if 'purse' in stats:
			# 	return f"This player does not have his inventory api enabled\n"
			# else:
			if 'current_profile_uuid' in stats:
				ret_str = self.get_profile_details(mc_uuid, stats['current_profile_uuid'], ret_str)
			return ret_str
		except json.decoder.JSONDecodeError:
			return f"Hypixel api is offline or player not found :( Try again later"

	def __init__(self):
		self.mc_name = None


class CakeAuction:
	def ends_in(self) -> int:
		if self.bin:
			return 1  # insert fake value, because it is sorted better and when it ends is irrevelant
		else:
			return int(int(self.end) / 1000 - time.time())

	def get_year(self) -> int:
		item_lore = self.json['item_lore']
		reg = re.search(r'the (\d+)(?:st|nd|rd|th)', item_lore)
		if reg:
			return int(reg.group(1).replace(",", ""))
		else:
			print(item_lore)
			print("year error", item_lore)
			return -1

	def get_bidders(self):
		contains_my_bid = False
		top_bidder_uuid = None

		for bid in self.json['bids']:
			top_bidder_uuid = bid['bidder']
		# print(bid['bidder'])
		return top_bidder_uuid

	def is_bin(self) -> bool:
		if "bin" in self.json and self.json['bin']:
			return True
		else:
			return False

	def is_sold(self):  # works only for bin auctions
		if self.bin and self.highest_bid != 0:
			return True
		else:
			return False

	def __init__(self, json):
		self.json = json
		self.year = self.get_year()
		self.bin = self.is_bin()
		self.auctioneer_uuid = json['auctioneer']
		self.highest_bid = json['highest_bid_amount']
		self.price = round(max(json['highest_bid_amount'], json['starting_bid']) / 1000000, 3)
		self.end = json['end']
		self.top_bidder_uuid = self.get_bidders()
		self.id = json['uuid']  # auction id

		self.json = None


class Cakes:

	def get_latest_cake_year(self):
		latest_year = -1
		for key, cake in self.cakes.items():
			latest_year = max(cake.year, latest_year)

		self.latest_year = latest_year

	def extract_cake_auctions_from_json(self):
		cake_auction_dict = {}
		self.ah_pages_total = 0
		self.ah_incorrect_pages = 0
		for filename in os.listdir('auction'):
			self.ah_pages_total += 1
			with open('auction/' + filename, 'rb') as f:
				try:
					ah_dict = json.load(f)
				except:
					self.ah_incorrect_pages += 1
					print('INVALID FILE', filename)
					continue
				if ah_dict['success']:
					for auction in ah_dict['auctions']:
						if 'New Year Cake' in auction['item_name'].strip() and "bag" not in auction['item_name'].strip().lower():
							# if auction['auctioneer'] != CONF['my_mc_details']['uuid']:
							cake_auction_dict[auction['uuid']] = CakeAuction(auction)
				else:
					self.ah_incorrect_pages += 1
		return cake_auction_dict

	def get_current_cake_year(self) -> int:
		current_year = -1

		for key, cake in self.cakes.items():
			current_year = max(current_year, cake.year)

		return current_year

	def try_to_update_ah(self):
		# print("Skipping downloading AH because DEBUG")
		# return False
		if self.ah_last_updated + 120 < time.time():
			self.ah_last_updated = time.time()
			print("Updating AH")
			download_auctions()
			self.cakes = self.extract_cake_auctions_from_json()
			return True
		else:
			print("AH updating skipped")
			return False

	def __init__(self):
		self.ah_last_updated = time.time() - 99999
		self.cakes = None
		self.cakes = self.extract_cake_auctions_from_json()
		self.ah_incorrect_pages = 0
		self.ah_pages_total = 0

	def incorrect_download_warning(self):
		if self.ah_incorrect_pages != 0:
			return f"WARNING: INCOMPLETE DATA SHOWN, BECAUSE HYPIXEL API RETURNED INCOMPLETE DATA! Invalid pages {self.ah_incorrect_pages} out of {self.ah_pages_total} pages total\n"
		elif self.ah_pages_total == 0:
			return f"WARNING: HYPIXEL API RETURNED NO DATA for some reason (it is currently probably down). INCOMPLETE DATA SHOWN (if any)\n"
		else:
			return ""

	def rarest_cakes_in_ah(self):
		cake_counts = {}
		current_year = self.get_current_cake_year()

		for year in range(current_year + 1):
			cake_counts[year] = 0

		for key, cake in self.cakes.items():
			cake_counts[cake.year] += 1

		print("Year count_in_AH")
		for year, count in cake_counts.items():
			print(str(year).ljust(4), count)

		print("\n")

		cake_counts = {k: cake_counts[k] for k in sorted(cake_counts, key=cake_counts.get)}  # sort dictionary

		print("Year count_in_AH")
		for year, count in cake_counts.items():
			print(str(year).ljust(4), count)

	def bin_prices_to_var(self, ignore_name=None):
		if not self.try_to_update_ah():
			print("DEBUG: Updating AH skipped, because it was updated in the last 2 minutes")

		if ignore_name is not None:
			ignore_name_uuid = get_uuid_from_mc_name(ignore_name)
		else:
			ignore_name_uuid = None

		self.bin_cake_years = {}
		# cake_counts = {}
		for key, cake in self.cakes.items():
			if cake.bin:
				if ignore_name_uuid is None or cake.auctioneer_uuid != ignore_name_uuid:
					if cake.year not in self.bin_cake_years:
						self.bin_cake_years[cake.year] = [cake]
					else:
						self.bin_cake_years[cake.year].append(cake)

		# if cake.year not in cake_counts:
		# 	cake_counts[cake.year] = 1
		# else:
		# 	cake_counts[cake.year] += 1

		self.max_year_found_in_dict = max(self.bin_cake_years, key=int)

		self.bin_cheapest_cakes = {}

		for year in range(self.max_year_found_in_dict + 1):
			self.bin_cheapest_cakes[year] = []
			year_cake_list = []
			if year in self.bin_cake_years:
				# add cakes to temp list
				for cake in self.bin_cake_years[year]:
					year_cake_list.append((cake.price, cake.id, cake))

				# sort cakes by price and get 5 cheapest
				year_cake_list_5_cheapest = sorted(year_cake_list)[:5]

				self.bin_cheapest_cakes[year] = year_cake_list_5_cheapest

	async def split_and_send(this, ctx, msg):
		# span = 20
		# words = msg.split("\n")
		splited = split_message(msg)
		# splited = ["\n".join(words[i:i + span]) for i in range(0, len(words), span)]
		# pprint(splited)
		for split in splited:
			# print(split + "\n")
			await ctx.send(f"```diff\n{split}```")



	async def analyze_bin_prices(self, ctx, ignore_name=None):
		self.bin_prices_to_var(ignore_name)

		ret_str = ""
		ret_str += self.incorrect_download_warning()

		table = TablePrint((5, 5, 30, 8, 20))
		ret_str += table.print_row(["Year", "BINs", "5 cheapest bins", "Cheapest auctioneer"])

		for year in range(self.max_year_found_in_dict + 1):
			year_cake_list = []
			if year in self.bin_cake_years:
				year_cake_list_5_cheapest_str = ""
				for cake_price, cake_id, cake in self.bin_cheapest_cakes[year]:
					year_cake_list_5_cheapest_str += str(cake_price) + " "
				ret_str += table.print_row([year, str(len(self.bin_cake_years[year])), year_cake_list_5_cheapest_str,
										        get_mc_name_from_uuid(
												self.bin_cheapest_cakes[year][0][2].auctioneer_uuid)])

		await self.split_and_send(ctx, ret_str)
		# span = 20
		# words = ret_str.split("\n")
		# splited = ["\n".join(words[i:i+span]) for i in range(0, len(words), span)]
		# # pprint(splited)
		# for split in splited:
		# 	# print(split + "\n")
		# 	await ctx.send(f"```{split}```")

		# for year in range(max_year_found_in_dict + 1):
		#
		# 	count_all = "-----"   ,
		# 	if year in cake_years:
		# 		min_p = 999999999
		# 		max_p = -1
		# 		for cake in cake_years[year]:
		# 			if cake.price < min_p:
		# 				cheapest_bins[cake.year] = cake
		#
		# 			min_p = min(min_p, cake.price)
		# 			max_p = max(max_p, cake.price)
		#
		# 		if year in cake_counts:
		# 			count_all = cake_counts[year]
		#
		# 		ret_str += table.print_row([year, str(len(cake_years[year])) + " / " + str(count_all), min_p, max_p, "/ah " +  get_mc_name_from_uuid(cheapest_bins[year].auctioneer_uuid)])
		# else:
		# 	ret_str += table.print_row([year, "-----", count_all])

		if ctx is None:
			print(ret_str)

	# else:
	# 	span = 20
	# 	words = ret_str.split("\n")
	# 	splited = ["\n".join(words[i:i+span]) for i in range(0, len(words), span)]
	# 	# pprint(splited)
	# 	for split in splited:
	# 		# print(split + "\n")
	# 		await ctx.send(f"```{split}```")

	# return f"```{ret_str}```"

	async def analyze_undercuts(self, ctx, name=None):
		if name is not None:
			name_uuid = get_uuid_from_mc_name(name)
		ret_str = ""
		# if not self.try_to_update_ah():
		# 	ret_str += "DEBUG: Updating AH skipped, because it was updated in the last 2 minutes\n"
		self.bin_prices_to_var(name)
		# self.bin_cheapest_cakes[]


		name_owned_cakes = {}
		name_best_offers = {}
		for uuid, cake in self.cakes.items():
			if cake.auctioneer_uuid == name_uuid:
				if cake.bin:

					if cake.year in name_best_offers:
						name_owned_cakes[cake.year].append(cake.year)
						name_best_offers[cake.year] = max(name_best_offers[cake.year], cake.price)
					else:
						name_owned_cakes[cake.year] = []
						name_owned_cakes[cake.year].append(cake.year)
						name_best_offers[cake.year] = cake.price

		# name_owned_cakes = sorted(name_owned_cakes)

		# for each cake year in ah
		found_undercuts = False
		for year in range(999):
			if year in name_owned_cakes:
				name_offer_in_milions = name_best_offers[year]


				# loop all cakes in ah
				found_undercut = False
				for uuid, cake in self.cakes.items():
					if cake.bin:
						if cake.year == year:
							if cake.price < name_offer_in_milions:
								if not found_undercuts:
									ret_str += f"Undercut results for {name}:\n\n"
									found_undercuts = True

								if not found_undercut:
									ret_str += f"--- {year} - {str(name_offer_in_milions)} ---\n"

								ret_str += f"Undercut - {str(cake.price).ljust(5)} - {get_mc_name_from_uuid(cake.auctioneer_uuid)}\n"
								found_undercut = True

				if found_undercut:
					ret_str += "\n"

		if not found_undercuts:
			ret_str += f"No undercuts found for {name}\n"
		# for ends_in, cake_year, cake_id, cake in name_owned_cakes:
		# 	print(cake_year)

		await self.split_and_send(ctx, ret_str)
		# print(ret_str)
		#


	async def auctions_ending_soon(self, ctx, auctioneer=None, top_bidder=None):
		if auctioneer is not None:
			auctioneer_uuid = get_uuid_from_mc_name(auctioneer)

		if top_bidder is not None:
			top_bidder_uuid = get_uuid_from_mc_name(top_bidder)
		ret_str = ""

		if not self.try_to_update_ah():
			ret_str += "DEBUG: Updating AH skipped, because it was updated in the last 2 minutes\n"

		ret_str += self.incorrect_download_warning()

		self.bin_prices_to_var(auctioneer)

		table = TablePrint((2, 10, 5, 10, 10, 22, 18, 10))
		list_not_sorted = []
		list_to_print = []
		rows_to_print = 500

		if top_bidder is not None or top_bidder is not None:
			rows_to_print = 1000

		for uuid, cake in self.cakes.items():
			ends_in = cake.ends_in()
			if ends_in < -60:
				continue

			if (auctioneer is None and top_bidder is None) and cake.bin:
				continue

			if auctioneer is not None and auctioneer_uuid != cake.auctioneer_uuid:
				continue

			if top_bidder is not None and top_bidder_uuid != cake.top_bidder_uuid:
				continue

			list_not_sorted.append((ends_in, cake.year, cake.id, cake))

		list_sorted = sorted(list_not_sorted)

		counter = 0
		for ends_in, cake_year, cake_id, cake in list_sorted:
			if counter == rows_to_print:
				break

			ends_in = cake.ends_in()

			auctioneer = get_mc_name_from_uuid(cake.auctioneer_uuid)

			if cake.top_bidder_uuid:
				top_bidder = get_mc_name_from_uuid(cake.top_bidder_uuid)
			else:
				top_bidder = ""

			if cake.bin:
				time_e = "BIN"
			else:
				time_e = str(seconds_to_hours_minutes_seconds(ends_in))

			cheapest_bin = "---"
			if cake.year in self.bin_cheapest_cakes:
				try:
					cheapest_bin = self.bin_cheapest_cakes[cake.year][0][2].price
				except:
					pass

			if cheapest_bin == "---" or cake.price <= cheapest_bin:
				is_cheapest = '+'
			else:
				is_cheapest = '-'

			list_to_print.append([is_cheapest, time_e, cake.year, cake.price, cheapest_bin, str(auctioneer), top_bidder])
			counter += 1

		ret_str += table.print_row([".", "Time", "year", "price", "ch. bin", "auctioneer", "top bidder"])

		for row_to_print in list_to_print:
			ret_str += table.print_row(row_to_print)
		ret_str += "\n"

		await self.split_and_send(ctx, ret_str)

	# print(ret_str)
	# return f"```{ret_str}```"

	def top(self, ctx=None):
		ret_str = ""

		if not self.try_to_update_ah():
			ret_str += "DEBUG: Updating AH skipped, because it was updated in the last 2 minutes\n"

		ret_str += self.incorrect_download_warning()

		top_bidders_uuid = {}
		top_auctioneers_uuid = {}

		for uuid, cake in self.cakes.items():
			temp_cake_bidder_uuid = cake.top_bidder_uuid
			if temp_cake_bidder_uuid is not None:
				if temp_cake_bidder_uuid in top_bidders_uuid:
					top_bidders_uuid[temp_cake_bidder_uuid] = top_bidders_uuid[temp_cake_bidder_uuid] + 1
				else:
					top_bidders_uuid[temp_cake_bidder_uuid] = 1

		for uuid, cake in self.cakes.items():
			temp_cake_auctioneer_uuid = cake.auctioneer_uuid
			if temp_cake_auctioneer_uuid in top_auctioneers_uuid:
				top_auctioneers_uuid[temp_cake_auctioneer_uuid] += 1
			else:
				top_auctioneers_uuid[temp_cake_auctioneer_uuid] = 1

		# sort by value
		top_bidders_uuid = {k: v for k, v in sorted(top_bidders_uuid.items(), key=lambda item: item[1], reverse=True)}
		top_auctioneers_uuid = {k: v for k, v in
								sorted(top_auctioneers_uuid.items(), key=lambda item: item[1], reverse=True)}

		table = TablePrint((9, 18, 15))
		ret_str += "\nMost top bids:\n"
		ret_str += table.print_row(["top bids", "name", "online/offline"])
		i = 0
		for uuid, count in top_bidders_uuid.items():
			mc_name = get_mc_name_from_uuid(uuid)

			online_status = is_player_online(mc_name)
			ret_str += table.print_row([count, mc_name, online_status])
			if i == 15:
				break
			i += 1

		ret_str += "\nTop auctioneers:\n"
		ret_str += table.print_row(["auctions", "name", "online/offline"])
		i = 0
		for uuid, count in top_auctioneers_uuid.items():
			mc_name = get_mc_name_from_uuid(uuid)

			online_status = is_player_online(mc_name)
			ret_str += table.print_row([count, mc_name, online_status])
			if i == 15:
				break
			i += 1

		return f"```{ret_str}```"


# print(uuid_add_dashes(SLADA_UUID))
# download_auctions()
cakes_obj = Cakes()
# cakes_obj.analyze_undercuts(None, "Slada")
# cakes_obj.analyze_undercuts(None, "P0tchi")
# cakes_obj.analyze_undercuts(None, "SkillGrind")
# exit()
# cakes_obj.analyze_bin_prices(None, None)
# cakes_obj.analyze_bin_prices(None, "cillian96470")
#
# cakes_obj.auctions_ending_soon("cillian96470")
# exit(0)
# cakes_obj.analyze_bin_prices()
# print(cakes_obj.auctions_ending_soon())
# print(cakes_obj.auctions_ending_soon("Slada"))
# print(cakes_obj.auctions_ending_soon("Brumby98"))
# cakes_obj.top(None)
# exit(0)


# print(InventoryImporter().offer_cakes("P0tchi"))
# print(InventoryImporter().offer_cakes("SkillGrind"))
# print(InventoryImporter().offer_cakes("Brumby98"))
# print(InventoryImporter().offer_cakes("cillian96470"))
# print(InventoryImporter().offer_cakes("Slada"))
#

# print("out:", InventoryImporter().offer_cakes("taftaf1"))
# exit(0)

bot = commands.Bot(command_prefix=COMMAND_PREFIX, help_command=None)


@bot.event
async def on_message(message):
	print(message.content)
	await bot.process_commands(message)


@bot.event
async def on_ready():  # This function will be run by the discord library when the bot has logged in
	print("Logged in as " + bot.user.name)


# @bot.command()
# async def ping(ctx):
# 	latency = bot.latency
# 	await ctx.send(latency)

# @bot.command()
# async def h(ctx):
# 	await ctx.send("Available commands:\n!uuid Slada - returns UUID")

async def is_dm(ctx):
	#print(ctx.author.id)
	deny_author_ids = []  # copy author id from discord

	if ctx.author.id in deny_author_ids:
		return True  # do not allow commands from these users


	if ctx.message.channel.id not in ALLOWED_CHANNEL_IDS:
		print("not in allowed channel")
		return True  # not correct channel ID, ignore command

	if ctx.guild is None:
		await ctx.send("Don't be shy! Talk with me in bot-channel!")
		return True
	else:
		return False


@bot.command()
async def col(ctx, mc_name):
	if await is_dm(ctx):
		return
	msg = InventoryImporter().offer_cakes(mc_name)
	if len(msg) > 1995:
		await cakes_obj.split_and_send(ctx, msg.replace('```', ''))
	else:
		await ctx.send(msg)



@bot.command()
async def top(ctx):
	if await is_dm(ctx):
		return

	await ctx.send(cakes_obj.top(None))


# @bot.command()
# async def uuid(ctx, mc_name):
# 	mc_uuid = get_uuid_from_mc_name(mc_name)
# 	await ctx.send(f"UUID: {mc_uuid}")

# @bot.command()
# async def hello(ctx):
# 	await ctx.send("Hello everyone!")

# @bot.command()
# async def shutdown(ctx):
# 	await ctx.send("Bye!")

@bot.command()
async def uc(ctx, mc_name=None):
	if await is_dm(ctx):
		return

	if mc_name is not None:
		await cakes_obj.analyze_undercuts(ctx, mc_name)
	else:
		await ctx.send("Invalid syntax, use !uc NAME")

@bot.command()
async def undercuts(ctx, mc_name=None):
	if await is_dm(ctx):
		return

	if mc_name is not None:
		await cakes_obj.analyze_undercuts(ctx, mc_name)
	else:
		await ctx.send("Invalid syntax, use !undercuts NAME")



@bot.command()
async def bins(ctx, mc_name=None):
	if await is_dm(ctx):
		return

	await cakes_obj.analyze_bin_prices(ctx, mc_name)


# await ctx.send(cakes_obj.analyze_bin_prices())

@bot.command()
async def soon(ctx):
	if await is_dm(ctx):
		return

	await cakes_obj.auctions_ending_soon(ctx)


# await ctx.send(cakes_obj.analyze_bin_prices())

@bot.command()
async def ah(ctx, name=None):
	if await is_dm(ctx):
		return

	if name is not None:
		await cakes_obj.auctions_ending_soon(ctx, name)
	else:
		await ctx.send("Invalid syntax, use !ah NAME")

@bot.command()
async def version(ctx, name=None):
	if await is_dm(ctx):
		return
	
	await ctx.send(VERSION_STRING)


@bot.command()
async def tb(ctx, name=None):
	if await is_dm(ctx):
		return

	if name is not None:
		await cakes_obj.auctions_ending_soon(ctx, None, name)
	else:
		await ctx.send("Invalid syntax, use !bids NAME")


@bot.command()
async def help(ctx):
	if await is_dm(ctx):
		return

	help = """
Deprecation warning:
This cake bot is deprecated. That means, that I (Slada) am not playing the game anymore and I can't improve the bot. I will try to keep the bot online and do small bug fixes. I promise, that the bot will stay online at least till 2022-01-01.

Turquoise_Fish sadly isn't working on a replacement bot :(

Available commands:
```
!ah NAME
!tb NAME
!soon
!bins
!bins NAME_TO_EXCLUDE
!top
!col NAME
!help
!undercuts NAME
```

```!ah NAME```-it allows you to quickly optimize your auctions, because only cheapest bin sells.
-bins in cheapest bins column don't include your bins (same as !bins NAME_TO_EXCLUDE command)

```!tb NAME```- shows auctions where player NAME is top bidder

```!soon```-shows first 50 cakes ending soon

```!bins```-Analyses current bin prices
-Shows 5 cheapest bins
-Shows name of the cheapest bin auctioneer

```!bins NAME_TO_EXCLUDE```-Same as !bins without parameter, but it filters out you bins from specified player (you often don't need to see your bins)

```!top```-Shows current top bidder leaderboard
-Shows players who currently sells the most amount of cakes in AH

```!col NAME```-sky lea for cakes :)
-shows online status, profile name, coins in purse, ah bids, special auctions bought/sold, collected unique cakes in the inventory, missing cakes and amount of cakes needed to complete the bag.
-duplicate cakes in inventory are not shown.
-to refresh inventory api, tell the player you are inspecting to revisit you.
-shows pies too :)

```!help```-shows this message

```!undercuts NAME```-shows better BIN offers that your worst BIN offer
"""
	await ctx.send(help)


# Run the discord bot
bot.run(DISCORD_API_KEY)