#!/bin/bash
set -e

export HOME=/home/ops

sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

sudo touch /etc/yum.repos.d/logstash.repo
sudo chmod 777 /etc/yum.repos.d/logstash.repo

sudo echo "[logstash-8.x]" > /etc/yum.repos.d/logstash.repo
sudo echo "name=Elastic repository for 8.x packages" >> /etc/yum.repos.d/logstash.repo
sudo echo "baseurl=https://artifacts.elastic.co/packages/8.x/yum" >> /etc/yum.repos.d/logstash.repo
sudo echo "gpgcheck=1" >> /etc/yum.repos.d/logstash.repo
sudo echo "gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch" >> /etc/yum.repos.d/logstash.repo
sudo echo "enabled=1" >> /etc/yum.repos.d/logstash.repo
sudo echo "autorefresh=1" >> /etc/yum.repos.d/logstash.repo

sudo yum install -y -q logstash
