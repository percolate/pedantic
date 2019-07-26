FROM python:3.6-alpine

WORKDIR /pedantic
ENV PYTHONPATH /pedantic

RUN apk add --update curl nodejs yarn bash

COPY requirements.txt package.json yarn.lock ./

RUN pip install -r requirements.txt

ENV NODE_PATH=/node_modules
RUN yarn --modules-folder $NODE_PATH && yarn cache clean

ENV PORT 5000
EXPOSE $PORT

COPY bin/pedantic bin/pedantic
COPY cli/ cli/
COPY pedantic/ pedantic/

ENTRYPOINT ["bin/pedantic"]
