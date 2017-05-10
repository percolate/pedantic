# Pedantic
# Version           0.0.1

FROM python:3.6.1-alpine
LABEL Description="This image is used to start the local Pendantic service." Author="Julien Funk" Version="0.0.1"

ADD pedantic/ requirements.txt /
RUN pip install -r requirements.txt
ENTRYPOINT ["./pedantic", "file_params/schema.json", "--whitelist=file_params/whitelist.json"]