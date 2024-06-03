FROM debian:bookworm-slim as base

ENV LANG=en_EN.UTF-8

RUN apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests --allow-unauthenticated -y \
        gnupg \
        ca-certificates \
        wget \
        locales \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    # Add the current key for package downloading
    # Please refer to QGIS install documentation (https://www.qgis.org/fr/site/forusers/alldownloads.html#debian-ubuntu)
    && mkdir -m755 -p /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg \
    # Add repository for latest version of qgis-server
    # Please refer to QGIS repositories documentation if you want other version (https://qgis.org/en/site/forusers/alldownloads.html#repositories)
    && echo "deb [signed-by=/etc/apt/keyrings/qgis-archive-keyring.gpg] https://qgis.org/debian bookworm main" | tee /etc/apt/sources.list.d/qgis.list \
    && apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests --allow-unauthenticated -y \
        python3-pip qgis python3-qgis python3-qgis-common python3-venv python3-pytest python3-mock qttools5-dev-tools \
        libtiff-dev g++ libboost-all-dev libeigen3-dev \
        build-essential curl \
        nodejs npm \
        git \
        xauth \
        xvfb \
        unzip \
        vim \
    && rm -rf /var/lib/apt/lists/*

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install && rm -rf ./aws awscliv2.zip

RUN npm install --global yarn
RUN useradd -m qgis

COPY fireanalyticstoolbox/requirements.txt /home/qgis/requirements.txt
RUN pip3 install --break-system-packages -r /home/qgis/requirements.txt
RUN pip3 install --break-system-packages importlib-metadata

COPY aws/package.json /home/qgis
COPY aws/yarn.lock /home/qgis
RUN cd /home/qgis && yarn

RUN git clone -b tif-test https://github.com/fire2a/C2F-W /usr/local/Cell2Fire
WORKDIR /usr/local/Cell2Fire/Cell2Fire
RUN make clean -f makefile.debian
RUN make install -f makefile.debian

COPY aws /usr/local/Cell2FireWrapper
RUN mv /home/qgis/node_modules /usr/local/Cell2FireWrapper/node_modules
WORKDIR /usr/local/Cell2FireWrapper
RUN yarn && yarn build


ENV QGIS_PREFIX_PATH /usr
ENV QGIS_SERVER_LOG_STDERR 1
ENV QGIS_SERVER_LOG_LEVEL 2

WORKDIR /home/qgis

ENV QT_QPA_PLATFORM offscreen
RUN mkdir -p /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/


RUN git clone https://github.com/fire2a/fire2a-lib /home/qgis/fire2a
COPY fireanalyticstoolbox /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a
RUN mkdir /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/fire2a
RUN cp /home/qgis/fire2a/src/fire2a/meteo.py /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/fire2a/
RUN cp /home/qgis/fire2a/src/fire2a/raster.py /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/fire2a/
RUN cp /home/qgis/fire2a/src/fire2a/utils.py /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/fire2a/
RUN cp /home/qgis/fire2a/src/fire2a/__init__.py /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/fire2a/
RUN mkdir -p /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/simulator/C2F/Cell2Fire/
RUN cp /usr/local/Cell2Fire/Cell2Fire/Cell2Fire /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/simulator/C2F/Cell2Fire/Cell2Fire.Linux.x86_64
RUN chown qgis:qgis /home/qgis -R
USER qgis

RUN cd /home/qgis/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fire2a/ && grep -Rl --include=*py "from fire2a" | tee will.change | xargs -I {} sed -i "s/^from fire2a/from .fire2a/" {}
RUN qgis_process plugins enable fire2a

FROM base as test
CMD ["node", "/usr/local/Cell2FireWrapper/build/test"]

FROM base as qgis
ENTRYPOINT ["node", "/usr/local/Cell2FireWrapper/build/main"]

