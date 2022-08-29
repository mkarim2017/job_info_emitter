ARG TAG=latest
FROM hysds/pge-base:${TAG}

MAINTAINER Mohammed Karim (mkarim) "mkarim@jpl.nasa.gov"
LABEL description="MAAP HEC Data Emitter"

ARG HOME=/home/ops

ENV PATH=$HOME/verdi/bin:${PATH} 

# link configs
# RUN set -ex \
# && ln -sf /home/ops/verdi/etc/celeryconfig.py /home/ops/verdi/ops/hysds/celeryconfig.py

# set default supervisord conf and copy includes
COPY --chown=ops:ops ./supervisord.conf /home/ops/verdi/etc/supervisord.conf


RUN git clone -b develop https://github.com/mkarim2017/job_info_emitter.git $HOME/job_info_emitter
RUN git clone -b develop https://github.com/mkarim2017/SOAMC-SQS-Communicator.git $HOME/SOAMC-SQS-Communicator

RUN sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

RUN sudo touch /etc/yum.repos.d/logstash.repo
RUN sudo chmod 777 /etc/yum.repos.d/logstash.repo

RUN sudo echo "[logstash-8.x]" > /etc/yum.repos.d/logstash.repo
RUN sudo echo "name=Elastic repository for 8.x packages" >> /etc/yum.repos.d/logstash.repo
RUN sudo echo "baseurl=https://artifacts.elastic.co/packages/8.x/yum" >> /etc/yum.repos.d/logstash.repo
RUN sudo echo "gpgcheck=1" >> /etc/yum.repos.d/logstash.repo
RUN sudo echo "gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch" >> /etc/yum.repos.d/logstash.repo
RUN sudo echo "enabled=1" >> /etc/yum.repos.d/logstash.repo
RUN sudo echo "autorefresh=1" >> /etc/yum.repos.d/logstash.repo

RUN sudo yum install -y -q logstash

RUN sudo chown --recursive logstash.logstash /usr/share/logstash
RUN sudo chmod 777 --recursive /usr/share/logstash/data

RUN sudo chown --recursive logstash.logstash /var/log/logstash
RUN sudo chmod 777 --recursive /var/log/logstash

RUN sudo chown --recursive logstash.logstash /var/lib/logstash
RUN sudo chmod 777 --recursive /var/lib/logstash

#COPY install_Logstash.sh /usr/local/bin/install_Logstash.sh
#RUN sudo chmod +x /usr/local/bin/install_Logstash.sh
#CMD ["install_Logstash.sh"]

# set entrypoint
COPY entrypoint* /
ENTRYPOINT ["/entrypoint_common.sh"]

EXPOSE 5000
WORKDIR $HOME
CMD ["supervisord"]
