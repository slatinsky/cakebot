# Cake bot
Discord bot to analyze new year cake market in Hypixel Skyblock.

**Warnings**
- very old code that was made in `2020-08`! But most of it still works as of `2023-02-20`. Also I am not playing Skyblock anymore, so I won't add new features to this bot - it relies on the community to make pull requests.
- The library used doesn't support discord slash commands. You need to enable message content intent in the Discord developer portal.

Tested with Python 3.10 on Raspberry Pi 4b. But should work on any Linux machine.

## Features
Look at the bottom of the `main.py` for a list of commands.

## Setup
You can run the bot in a docker container or manually.

- Manual setup is recommended if you want to develop the bot.
- Docker setup is recommended for easy deployment.
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
### Short guide, how to contribute
- Fork the repository
- Create a new branch
- Implement your changes
- Commit and push the changes
- Create a pull request

If you find this project useful, please consider starring it here on GitHub :)