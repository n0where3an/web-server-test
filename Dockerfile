### File            : Dockerfile
### Description     : Test pod for testing installed kubernetes
### Author          : Michael Yasko
### Version history :

FROM python:3.12-slim
RUN mkdir -p /app/logs /opt/configs
WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["python3","-u", "server.py"]

COPY requirements_server.txt ./requirements_server.txt

RUN python -m pip install -U pip && \
    python -m pip install -r ./requirements_server.txt && \
    python -m pip cache purge

#    pip install --upgrade pip setuptools wheel && \

LABEL maintainer="n0where3an@gmail.com"

COPY server.py ./server.py
CMD ["1","5","text"]
#EOF
