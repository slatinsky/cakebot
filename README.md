# Cake bot
Discord bot to analyze new year cake market in hypixel skyblock

Tested on  python 3.10 
## Installing python dependencies

Install required python dependencies from requirements.txt:

    pip install -r requirements.txt

## Fill in the config.ini file
Copy `config.ini.example` to `config.ini` and fill in the values.
Don't use double quotes in the config file.

## running the script
tmux new -s cake
py main.py

# attach to session
tmux attach-session -t cake