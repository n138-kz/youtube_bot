FROM python:3.10
WORKDIR /tmp

COPY requirements.txt /tmp/
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY youtube_bot.py /tmp/
COPY .secret/ /tmp/
COPY .secret/config.json /tmp/.secret/
COPY ytb_help.json /tmp/
ADD log/ /tmp/log/

ENTRYPOINT [ "python3", "/tmp/youtube_bot.py" ]
