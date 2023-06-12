import json
import os
import time

import Utils
from TablePrint import TablePrint
from CakeAuction import CakeAuction
from utils.LogController import LogController

class Cakes:

    def __init__(self):
        self.ah_last_updated = time.time() - 99999
        self.cakes = None
        self.cakes = self.extract_cake_auctions_from_json()
        self.ah_incorrect_pages = 0
        self.ah_pages_total = 0
        self.utils = Utils.Utils()
        self.logger = LogController().get_logger()

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
                    self.logger.error(f"Invalid file: {filename}")
                    continue
                if ah_dict['success']:
                    for auction in ah_dict['auctions']:
                        if 'New Year Cake' in auction['item_name'].strip() and "bag" not in auction[
                            'item_name'].strip().lower():
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
        if self.ah_last_updated + 120 < time.time():
            self.ah_last_updated = time.time()
            self.logger.info("Updating AH")
            self.utils.download_auctions()
            self.cakes = self.extract_cake_auctions_from_json()
            return True
        else:
            self.logger.info("AH updating skipped")
            return False

    def incorrect_download_warning(self):
        if self.ah_incorrect_pages != 0:
            self.logger.warn(msg=f"WARNING: INCOMPLETE DATA SHOWN, BECAUSE HYPIXEL API RETURNED INCOMPLETE DATA! "
                                 f"Invalid pages " f"{self.ah_incorrect_pages} out of {self.ah_pages_total} pages "
                                 f"total\n ")
            return f"WARNING: INCOMPLETE DATA SHOWN, BECAUSE HYPIXEL API RETURNED INCOMPLETE DATA! Invalid pages " \
                   f"{self.ah_incorrect_pages} out of {self.ah_pages_total} pages total\n "
        elif self.ah_pages_total == 0:
            self.logger.warn(msg=f"HYPIXEL API RETURNED NO DATA for some reason (it is currently probably down). "
                                 f"INCOMPLETE DATA SHOWN (if any)\n")
            return f"WARNING: HYPIXEL API RETURNED NO DATA for some reason (it is currently probably down). " \
                   f"INCOMPLETE DATA SHOWN (if any)\n"
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
            ignore_name_uuid = self.utils.get_uuid_from_mc_name(ignore_name)
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
                                            self.utils.get_mc_name_from_uuid(
                                                self.bin_cheapest_cakes[year][0][2].auctioneer_uuid)])

        return ret_str

    async def analyze_undercuts(self, ctx, name=None):
        if name is not None:
            name_uuid = self.utils.get_uuid_from_mc_name(name)
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

                                ret_str += f"Undercut - {str(cake.price).ljust(5)} - {self.utils.get_mc_name_from_uuid(cake.auctioneer_uuid)}\n"
                                found_undercut = True

                if found_undercut:
                    ret_str += "\n"

        if not found_undercuts:
            ret_str += f"No undercuts found for {name}\n"
        # for ends_in, cake_year, cake_id, cake in name_owned_cakes:
        # 	print(cake_year)

        return ret_str

    # print(ret_str)
    #

    async def auctions_ending_soon(self, ctx, auctioneer=None, top_bidder=None):
        if auctioneer is not None:
            auctioneer_uuid = self.utils.get_uuid_from_mc_name(auctioneer)

        if top_bidder is not None:
            top_bidder_uuid = self.utils.get_uuid_from_mc_name(top_bidder)
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

            auctioneer = self.utils.get_mc_name_from_uuid(cake.auctioneer_uuid)

            if cake.top_bidder_uuid:
                top_bidder = self.utils.get_mc_name_from_uuid(cake.top_bidder_uuid)
            else:
                top_bidder = ""

            if cake.bin:
                time_e = "BIN"
            else:
                time_e = str(Utils.seconds_to_hours_minutes_seconds(ends_in))

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

            list_to_print.append(
                [is_cheapest, time_e, cake.year, cake.price, cheapest_bin, str(auctioneer), top_bidder])
            counter += 1

        ret_str += table.print_row([".", "Time", "year", "price", "ch. bin", "auctioneer", "top bidder"])

        for row_to_print in list_to_print:
            ret_str += table.print_row(row_to_print)
        ret_str += "\n"

        return ret_str

    # print(ret_str)
    # return f"```{ret_str}```"

    def top(self):
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
            mc_name = self.utils.get_mc_name_from_uuid(uuid)

            online_status = self.utils.is_player_online(mc_name)
            ret_str += table.print_row([count, mc_name, online_status])
            if i == 15:
                break
            i += 1

        ret_str += "\nTop auctioneers:\n"
        ret_str += table.print_row(["auctions", "name", "online/offline"])
        i = 0
        for uuid, count in top_auctioneers_uuid.items():
            mc_name = self.utils.get_mc_name_from_uuid(uuid)

            online_status = self.utils.is_player_online(mc_name)
            ret_str += table.print_row([count, mc_name, online_status])
            if i == 15:
                break
            i += 1

        return f"```{ret_str}```"
