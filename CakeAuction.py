import re
import time

from utils.LogController import LogController


class CakeAuction:
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

        self.logger = LogController().get_logger()

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
