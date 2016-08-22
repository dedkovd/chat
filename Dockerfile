FROM ubuntu:14.04
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install python python-tornado python-redis redis-server -y
RUN service redis-server start
ADD chat.py /opt/chat.py
ADD dal.py /opt/dal.py
ADD static/index.html /opt/static/index.html
ADD static/chat.js /opt/static/chat.js
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 8888
ENTRYPOINT ["/usr/bin/python"]
CMD ["/opt/chat.py"]
