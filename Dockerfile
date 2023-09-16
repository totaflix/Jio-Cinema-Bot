FROM python:3.9.5-slim-buster

RUN mkdir ./app
RUN chmod 777 ./app
WORKDIR /app

RUN apt -qq update

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata

# For wine64 and wine32
RUN apt-get -qq install wine
RUN dpkg --add-architecture i386 
RUN apt-get -qq update 
RUN apt-get -qq -y install wine32 winbind wine64 wget

# For mkvmerge
RUN wget -q -O - https://mkvtoolnix.download/gpg-pub-moritzbunkus.txt | apt-key add - && \
    wget -qO - https://ftp-master.debian.org/keys/archive-key-10.asc | apt-key add -
RUN sh -c 'echo "deb https://mkvtoolnix.download/debian/ buster main" >> /etc/apt/sources.list.d/bunkus.org.list' && \
    sh -c 'echo deb http://deb.debian.org/debian buster main contrib non-free | tee -a /etc/apt/sources.list' && apt update && apt install -y mkvtoolnix

RUN apt-get -qq install -y python3 python3-pip ffmpeg git yt-dlp aria2


# COPY requirements.txt .
# COPY run.sh .
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "bot"]
