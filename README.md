# Cake bot

Discord bot to analyze new year cake market in Hypixel Skyblock.

**Maintenance mode**

- the bot was originally made in `2020-08`
- all commands are working as of `2023-09-02`, but am not playing Skyblock anymore, so no new big features are planned. You can still open pull requests if you want to add new features.

## Glossary

- BIN - buy it now
- AH - auction house
- TB - top bidder
- Year - the year of the new year cake
- Auctioneer - the player who listed the auction
- mc-name - minecraft name
- ch. bin - cheapest BIN price

## Commands

The bot is hosted in (invite only) `Hypixel New Year Cakes` discord server in the `#bot-commands` channel. Use bot commands in this channel.

### /bins

- Shows the current BIN prices for all cake types.


Example: 
```
/bins
```

```
Year BINs 5 cheapest bins               Cheapest auctioneer
1    8    89.999 90.0 95.0 95.0 96.0    SimpleSilence
2    1    100.0                         He_nEHEk
3    1    87.0                          FueledByMids
5    5    29.0 29.0 29.0 32.0 35.0      WarianaGrande
6    4    24.9 24.9 34.0 35.0           HaBoleo 
7    4    24.279 24.5 28.0 30.0         Seaniiiboy
8    4    28.25 28.279 37.0 40.0        FueledByMids
11   3    16.0 18.0 20.0                FueledByMids
...
```

### /ah \<mc-name\>

- Show current AH listings for a player.
- If the row is green, the cake price is lower than the cheapest BIN price.

```
/ah mc_name: skillgrind
```

```diff
. Time      year price     ch. bin   auctioneer            top bidder        
+ BIN       35   15.0      ---       SkillGrind                              
- BIN       100  50.0      41.779    SkillGrind                              
```

### /col \<mc-name\>

- Show the collection of new year cakes and spooky pies of a player.

```
/col Schroti
```

```
Schroti
Raspberry - Offline
Purse: 154.419 mil
```

```
AH
Bids: 23246
Special bought/sold: 21284/3251
```

```
Inventory
Found in inventory: 34, 274, 276, 289, 293
Not found in inventory: 0-33, 35-273, 275, 277-288, 290-292, 294-299
Needed cakes to complete the bag: 49
```

```
Spooky Pies:

Name             rank      yearpositionscore 
Schroti          mvp++     132 11936 130   
Schroti          mvp++     207 10361 272   
Schroti          mvp       210 8623  228   
Schroti          mvp++     216 6794  176   
Schroti          mvp++     217 9495  208   
``````

### /soon

- Shows auctions with new year cakes that will end soon.
- If the row is green, the cake price is lower than the cheapest BIN price.

Example:

```
/soon
```

```diff
Auctions ending soon:

. Time      year price     ch. bin   auctioneer            top bidder        
+ 0:41:01   42   3.064     ---       xLoloman              SleepyAmy         
+ 4:19:18   288  0.0       0.994     Amycakes312           Murphy040         
+ 4:35:56   203  0.0       ---       rutsjeb               ERBONE            
+ 4:35:59   185  0.0       1.999     rutsjeb               ERBONE            
+ 4:36:02   208  0.001     ---       rutsjeb               ERBONE            
+ 4:36:04   179  0.0       1.999     rutsjeb               ERBONE            
+ 4:36:10   210  0.0       ---       rutsjeb               ERBONE            
+ 4:36:13   233  0.0       ---       rutsjeb               ERBONE            
+ 10:41:14  72   0.967     3.25      Bush_on_Fire          Silly_Sans101     
+ 13:09:07  297  1.1       4.45      Tritanuim             PeanutButterKong  
+ 13:09:21  298  0.3       0.799     Tritanuim             MrTiger999        
+ 14:19:56  298  0.5       0.799     Solokiller452                           
- 17:33:46  282  2.0       0.994     ThE_hOrNeT_                             
+ 18:55:36  181  5.0       ---       Tigerrs                                 
+ 26:26:25  121  0.5       5.0       Creepersbegaming                        
+ 37:34:28  298  0.001     0.799     Cowardly9487          ERBONE            
```

### /top

- Shows the top 16 players with the most bids.
- Shows the top 16 players with the most auctions.
- `unknown` means that the player online status has been disabled in his API settings.

Example:

```
/top
```

```
Top auctioneers:

Most top bids:
top bids name              online/offline 
5        ERBONE            Offline        
3        Meisterkalle      Offline        
2        YORLE             Offline        
2        Silly_Sans101     Online         
2        minecrafterrors   Offline        
2        WLivesMatter      Offline        
2        Jabs_LN           Offline        
1        XxMrCheese        Offline        
1        751u              Offline        
1        PeanutButterKong  Offline        
1        Murphy040         Online         
1        Chopye            Offline        
1        goodrng           Offline        
1        undeadcoyote77    Offline        
1        MrTiger999        Offline        
1        sbx1              Unknown        

Top auctioneers:
auctions name              online/offline 
19       Munly             Online         
14       GoodGuyAL         Offline        
14       Papyrususus       Offline        
13       cillian96470      Online         
13       YSkyable          Offline        
11       PresidentBaker    Offline        
10       FueledByMids      Offline        
8        Seaniiiboy        Offline        
8        Dinip             Offline        
7        hunterpfiff       Offline        
7        SpigotHeadPlugin  Offline        
6        AmYours           Unknown        
6        rutsjeb           Offline        
6        WarianaGrande     Online         
5        NoWarNoGlory      Offline        
5        aziv              Online      
```


### /undercuts \<mc-name\>

- Lists BINs where the players BIN is more expensive than the cheapest BIN price.


Example:

```
/undercuts SkillGrind
```

```diff
Undercut results for SkillGrind:

--- 1 - 99.0 ---
Undercut - 97.99 - AfricanFlipFlap
Undercut - 98.0  - Koquip
Undercut - 95.0  - SDAFDASFE
Undercut - 95.0  - SDAFDASFE

--- 130 - 3.0 ---
Undercut - 2.0   - Hyorg
Undercut - 2.0   - ExpertiseX
```

Example (no undercuts found):

```
/undercuts Schroti
```

```
Undercuts for Schroti:

No undercuts found for Schroti
```

### /tb  \<mc-name\>

- Lists auctions where the player is the top bidder
- If the row is green, the cake price is lower than the cheapest BIN price.

Example:

```
/tb Silon_CZ
```

```diff
TB Overview for Silon_CZ:

. Time      year price     ch. bin   auctioneer            top bidder        
+ 11:50:09  264  0.1       ---       Bananagone            Silon_CZ          
+ 15:12:15  294  0.1       0.499     pjobird               Silon_CZ          
+ 25:27:16  293  0.1       4.9       JFEJ                  Silon_CZ          
+ 29:13:24  234  0.1       0.895     Hyperhuhn007          Silon_CZ          
+ 62:56:22  294  0.05      0.499     Talented_Tom          Silon_CZ          
```

Example (no top bids found):

```
/tb Schroti
```

```
Top bidder overview for Schroti:

No auctions found
```


### /ah \<mc-name\>

- Shows the current AH listings for a player.
- If the row is green, the cake price is lower than the cheapest BIN price.

Example:

```
/ah SkillGrind
```

```diff
AH data for SkillGrind:
. Time      year price     ch. bin   auctioneer            top bidder        
- BIN       1    99.0      97.99     SkillGrind                              
+ BIN       40   6.0       ---       SkillGrind                              
+ BIN       43   6.0       ---       SkillGrind                              
+ BIN       44   6.0       ---       SkillGrind                              
+ BIN       47   6.0       ---       SkillGrind                              
+ BIN       49   6.0       ---       SkillGrind                              
+ BIN       51   8.0       ---       SkillGrind                              
+ BIN       113  3.0       ---       SkillGrind                              
+ BIN       116  2.0       ---       SkillGrind                              
- BIN       130  3.0       2.0       SkillGrind                              
```

### /delcache

- The bot caches mapping between uuids and mc names, because this api is heavily rate limited.
- This command deletes the cache.
- Use is player name in the results is wrong. (because player changed his minecraft name)

Example:

```
/delcache
```

```
Deleted mcnames database - minecraft names will be fresh again
```


### /version

- Shows the current version of the bot (100 + commit count).
- Shows the current commit hash.
- Shows the current commit date.

Example:

```
/version
```

```
Bot Version
Bot version BETA 164 (826dbc5, 2023-09-02 00:16:26 +0000)
```

### /info

- Shows mini help for the bot.

Example:

```
/info
```

```
Status of this bot
The bot is currently maintained and worked on by @Schroti and @Slada, for any questions/improvements message/ping us!
```

```
Commands
Available commands:
/ah NAME
/tb NAME
/soon
/bins
/bins NAME_TO_EXCLUDE
/top
/col NAME
/info
/undercuts NAME
```

### /changelog

- Shows the changelog of the bot.
- Uses commit messages as changelog entries.

Example:

```
/changelog
```

```
last 10 commits:
v160: display full changelog again
v159: fix /version
...
```


## Setup
You can run the bot in a docker container or manually.

- Manual setup is recommended if you want to develop the bot.
- Docker setup is recommended for easy deployment.


You need to request [hypixel api key](https://developer.hypixel.net/dashboard/) and [discord bot api key](https://discord.com/developers/applications) - set the api keys in `config.ini.prod` file.

### Docker
```bash
git clone https://github.com/slatinsky/cakebot
cd cakebot
cp config.ini.example config.ini.prod
nano config.ini.prod
docker build -t cakebot .
docker run -d --name cakebot cakebot
```



### Manual setup

Make sure you have Python 3.10+ installed.

```bash
python3 --version
```

Clone the repository:
```bash
git clone https://github.com/slatinsky/cakebot
```

Install required python dependencies from `requirements.txt`:
```bash
python3 -m pip install -r requirements.txt
```
Copy `config.ini.example` as `config.ini` and fill in the values.
Don't use double quotes in the config file.

## Usage

To run the script:
```bash
python3 main.py
```

## License
GNU GENERAL PUBLIC LICENSE

This project is not affiliated with Hypixel or Mojang.
## Contributing

Feel free to open pull requests.

## Thanks

Thanks to [Schroti](https://github.com/Schroti) for helping me with the bot maintenance.

<details><summary><b>Short guide, how to contribute</b></summary>

- Fork the repository
- Create a new branch
- Implement your changes
- Commit and push your changes
- Create a pull request

</details>

If you find this project useful, give it a star ⭐. Thank you!