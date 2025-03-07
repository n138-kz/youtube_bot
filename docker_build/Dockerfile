FROM python:3.10
WORKDIR /tmp

COPY requirements.txt /tmp/
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY youtube_bot.py /tmp/
COPY .secret/ /tmp/

ENTRYPOINT [ "python3", "/tmp/youtube_bot.py" ]
