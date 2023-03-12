import base64
import io
import json
import re

import discord
import nbt
import requests

import Utils
from TablePrint import TablePrint


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
                        'year': str(pie_item_extra_attributes['event']).replace('spooky_festival_', '').replace(
                            'unanticipated_', 'e')}
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

    def get_stats_from_uuid(self, uuid: str):
        data = requests.get(
            "https://api.hypixel.net/skyblock/profiles?key=" + Utils.API_KEY + "&uuid=" + uuid).json()

        last_save = 0
        stats = {}

        if 'profiles' in data:
            for profile in data['profiles']:
                personal_profile = profile['members'][uuid]
                # print("PROF", personal_profile)
                # print(profile['cute_name'], personal_profile['last_save'])
                if profile['selected'] is True:
                    stats = self.get_stats(personal_profile, profile)
                    print(f"Found selected profile: {profile['cute_name']}")
                # print("skipped profile")
                else:
                    print(f"Profile {profile['cute_name']} is not selected")
        else:
            print('PROFILES NOT FOUND')
        # profile = data['profile']
        # personal_profile = data['profile']['members'][uuid]
        # stats = self.get_stats(data['profile'], profile)

        return stats

    #
    # 	# print(current_profile, current_profile_uuid)

    def get_inventory_details(self, mc_uuid: str, profile_uuid: str):

        inventory_embed = discord.Embed(title="Inventory", description="")
        pie_str = ""

        data = requests.get(
            'https://api.hypixel.net/skyblock/profile?key=' + Utils.API_KEY + '&profile=' + profile_uuid).json()
        current_member = data['profile']['members'][mc_uuid]

        inventories = []
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

        if 'ender_chest_contents' in current_member:
            if 'data' in current_member['ender_chest_contents']:
                inventories.append(current_member['ender_chest_contents']['data'])

        if not inventories:
            inventory_embed.description += "This player does not have his inventory api enabled"
            return

        cake_list = self.find_cakes_in_item_list(self.list_of_all_items_in_inventories(inventories))
        pie_list = self.find_pies_in_item_list(self.list_of_all_items_in_inventories(inventories))

        cake_set = set(cake_list)

        inventory_embed.description += f"Found in inventory: {Utils.list_to_ranges(sorted(list(cake_set)))}\n"

        not_owned_cakes = set()

        for i in range(0, Utils.MAX_CAKE_YEAR):
            if i not in cake_set:
                not_owned_cakes.add(i)

        inventory_embed.description += f"Not found in inventory: {Utils.list_to_ranges(sorted(list(not_owned_cakes)))}\n"
        count_needed = 54 - len(cake_set)
        inventory_embed.description += f"Needed cakes to complete the bag: {count_needed}\n"

        if len(pie_list) == 0:
            pie_str += "No spooky pies found"
        else:
            table = TablePrint((17, 10, 4, 6, 6))
            pie_str += table.print_row(["Name", "rank", "year", "position", "score"])
            for pie in pie_list:
                pie_str += table.print_row(
                    [pie['player'], pie['rank'], pie['year'], pie['position'] if (pie['position'] != "-1") else '?',
                     pie['score'] if (pie['score'] != "-1") else '?'])

        return inventory_embed, pie_str

    async def offer_cakes(self, mc_name, interaction):
        self.mc_name = mc_name

        await interaction.response.send_message(content=f"Loading data for player {mc_name}...")

        try:
            mc_uuid = Utils.get_uuid_from_mc_name(self.mc_name)
            stats = self.get_stats_from_uuid(mc_uuid)

            print("stats:" + str(stats))
            stats_embed = discord.Embed(title=mc_name)

            if 'current_profile' in stats:
                stats_embed.description = f"{stats['current_profile']} - {Utils.is_player_online(mc_name)}\n"

            if 'purse' in stats and stats['purse'] is not None:
                stats_embed.description += f"Purse: {Utils.k_to_mil(int(stats['purse']) / 1000)} mil\n"

            ah_embed = discord.Embed(title="AH", description="")

            if 'auctions_bids' in stats:
                ah_embed.description += f"Bids: {int(stats['auctions_bids'])}\n"

            if 'auctions_sold_special' not in stats:
                stats['auctions_sold_special'] = 0

            if 'auctions_bought_special' not in stats:
                stats['auctions_bought_special'] = 0

            ah_embed.description += f"Special bought/sold: " \
                                    f"{int(stats['auctions_bought_special'])}/{int(stats['auctions_sold_special'])}\n"

            # if 'purse' in stats:
            # 	return f"This player does not have his inventory api enabled\n"
            # else:
            if 'current_profile_uuid' in stats:
                inventory_embed, pie_str = self.get_inventory_details(mc_uuid, stats['current_profile_uuid'])

            await interaction.edit_original_response(embeds=[stats_embed, ah_embed, inventory_embed], content="")

            await interaction.channel.send("Spooky Pies:")
            if pie_str is not None:
                if len(pie_str) < 1995:
                    await interaction.channel.send(pie_str)
                else:
                    msgs = Utils.split_message(pie_str)
                    for msg in msgs:
                        await interaction.channel.send(f"```diff\n{msg}```")

        except json.decoder.JSONDecodeError:
            return f"Hypixel api is offline or player not found :( Try again later"

    def __init__(self):
        self.mc_name = None
