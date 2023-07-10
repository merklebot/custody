FROM python:3.10.6 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10.6

RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt update
RUN apt-get install -y nodejs
RUN npm install ipfs-car -g
WORKDIR /custody


ARG GOLANG_VERSION=1.20.5

#we need the go version installed from apk to bootstrap the custom version built from source
#RUN apt update && apt install gcc bash musl-dev
WORKDIR /tmp
RUN wget https://dl.google.com/go/go$GOLANG_VERSION.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go$GOLANG_VERSION.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin

WORKDIR /tmp
RUN rm go$GOLANG_VERSION.linux-amd64.tar.gz


RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN apt install jq libtool libhwloc-dev ocl-icd-opencl-dev --yes

WORKDIR /
RUN git clone https://github.com/filecoin-project/boost
WORKDIR boost
RUN make clean build
RUN make install





COPY --from=requirements-stage /tmp/requirements.txt /custody/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /custody/requirements.txt
COPY ./custody /custody/custody
COPY ./tmp /custody/tmp
COPY ./start.sh /custody/start.sh
WORKDIR /custody
ENTRYPOINT ["/bin/bash" ,"start.sh"]
