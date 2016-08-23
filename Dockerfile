FROM ubuntu:14.04
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install python python-tornado python-redis redis-server -y
ADD chat.py /opt/chat.py
ADD dal.py /opt/dal.py
ADD run.sh /opt/run.sh
RUN chmod +x /opt/run.sh
ADD static/index.html /opt/static/index.html
ADD static/chat.js /opt/static/chat.js
EXPOSE 8888
ENTRYPOINT ["/bin/bash"]
CMD ["/opt/run.sh"]
