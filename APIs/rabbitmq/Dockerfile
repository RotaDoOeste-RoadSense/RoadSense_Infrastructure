FROM rabbitmq:3.13-management

COPY rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY definitions.json /etc/rabbitmq/definitions.json

RUN chown rabbitmq:rabbitmq /etc/rabbitmq/*

# CMD padrão já inicia o server