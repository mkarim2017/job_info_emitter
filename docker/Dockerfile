ARG TAG=latest
FROM hysds/pge-base:${TAG}

MAINTAINER Mohammed Karim (mkarim) "mkarim@jpl.nasa.gov"
LABEL description="MAAP HEC Data Emitter"

ARG HOME=/home/ops

# link configs
RUN set -ex \
 && ln -sf /home/ops/verdi/etc/celeryconfig.py /home/ops/verdi/ops/hysds/celeryconfig.py

# set default supervisord conf and copy includes
COPY --chown=ops:ops ./supervisord.conf /home/ops/verdi/etc/supervisord.conf


RUN git clone -b develop https://github.com/mkarim2017/job_info_emitter.git $HOME/job_info_emitter
RUN git clone -b develop https://github.com/mkarim2017/SOAMC-SQS-Communicator.git $HOME/SOAMC-SQS-Communicator

COPY install_Logstash.sh /usr/local/bin/install_Logstash.sh
RUN sudo chmod +x /usr/local/bin/install_Logstash.sh
CMD ["install_Logstash.sh"]


# set entrypoint
COPY entrypoint* /
ENTRYPOINT ["/entrypoint-maap-hec.sh"]
EXPOSE 5000
WORKDIR $HOME
CMD ["supervisord"]
#CMD ["/bin/bash", "--login"]
