FROM ubuntu
MAINTAINER @mattdashj

RUN apt-get update
RUN apt-get install -y \
    python3 \
    python3-pip \
    git \
    && true
RUN pip3 install plotly
RUN mkdir ~/.plotly
COPY * /speedtest-cli/
CMD ["python3", "/speedtest-cli/speedtest.py", "--plotly"]
