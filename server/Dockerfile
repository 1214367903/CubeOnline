FROM pypy:3

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

RUN pip install -U pip
RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple
RUN pip config set install.trusted-host mirrors.aliyun.com

COPY . .
RUN pip install --no-cache-dir -r requirements.txt


CMD [ "pypy3", "./app.py" ]
