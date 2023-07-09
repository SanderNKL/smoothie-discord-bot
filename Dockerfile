FROM python:3.8-slim
RUN apt-get update \
  && apt-get install -y --no-install-recommends git \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /
RUN pip install -r /requirements.txt
RUN apt-get update && apt-get install -y ffmpeg

COPY . /Smoothie
RUN chmod +x /Smoothie/bot.py

WORKDIR /Smoothie
ENTRYPOINT [ "python", "-u", "bot.py"]