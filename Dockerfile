FROM ubuntu:20.04

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
RUN wget -O /usr/share/keyrings/gpg-pub-moritzbunkus.gpg https://mkvtoolnix.download/gpg-pub-moritzbunkus.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/gpg-pub-moritzbunkus.gpg] https://mkvtoolnix.download/ubuntu/ focal main" | tee /etc/apt/sources.list.d/mkvtoolnix.list
RUN echo "deb-src [signed-by=/usr/share/keyrings/gpg-pub-moritzbunkus.gpg] https://mkvtoolnix.download/ubuntu/ focal main" | tee -a /etc/apt/sources.list.d/mkvtoolnix.list
RUN apt-get update
RUN apt-get -qq install mkvtoolnix

RUN apt-get -qq install -y python3 python3-pip ffmpeg git yt-dlp aria2


# COPY requirements.txt .
# COPY run.sh .
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "bot"]
