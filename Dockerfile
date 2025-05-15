FROM python:latest

WORKDIR /homely-tools

COPY homely-tools /homely-tools

RUN pip install --upgrade pip
RUN pip install requests paho-mqtt python-socketio[client]\<5.0 pyyaml

ENV PYTHONPATH="${PYTHONPATH}:/homely-tools/API"
CMD [ "python3", "/homely-tools/mqtt/homely2mqtt.py", "-v" ]
