FROM python:3.11.1-alpine3.17
WORKDIR /app

# install git
RUN apk add git

# copy requirements.txt to the working directory
COPY requirements.txt .

# install dependencies from requirements.txt
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . .

# copy config.ini.prod to config.ini
COPY config.ini.prod config.ini

# command to run on container start
CMD [ "python", "./main.py" ]
