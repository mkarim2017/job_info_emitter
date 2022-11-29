# JOB INFO EMMITTER


## Overview

Job Info Emmitter emits job status and metrics information of a wpst end points. It communicates with the flex server to get the information and if there is a diff between present and previous information, it writes to a logfile.

logstash, running as separate process, reads the logfile and writes it to a sqs queue. A different logstash, running in maap-hec cluster, reads from the sqs queue and writes to a Elastic Search.

## Job Status Emmitter
on_endpoints/job_status_checker.py

How to Run:
It takes three arguments:

- --output_log: Output Log File Name with Full Path
- --server_ip: Flex Server IP Address. Default is localhost
- --server_port: Flex Server Port. Default is 5000
- --config: Optionally specify a config file with full path with other parameter infos

Example: python job_status_checker.py --output_log=ades-pbs-maaphec-dev-wpst-job.log

## Job Metrics Emmitter

on_endpoints/job_metrics_checker.py

How to Run:
It takes three arguments:

- --output_log: Output Log File Name with Full Path
- --server_ip: Flex Server IP Address. Default is localhost
- --server_port: Flex Server Port. Default is 5000
- --config: Optionally specify a config file with full path with other parameter infos

Example: python job_metrics_checker.py --output_log=ades-pbs-maaphec-dev-wpst-metrics.log

## Logstash

There are two sets of logstash running in enpoints, for job and metrics respectively. One reads the log from job status emmiter and other from job metrics emmiter. They write to job status queue and job metrics queue respectively. 

There are another two sets of logstash run in maap-hec cluster which read from job status queue and job metrics queue respectively and write to elastic search.

Please see cluster_provisioning/logstash/ for configuration of the logstash.conf file for all the logstash processes.


## SQS Queues
SQS queues are used to communicate between client and wpst_client_daemon. User can  create necessary queues using the terraform or python script in cluster_provisioning directory. The two quesues used for WPST Communicator are request queue and reply queue. These queue names are specified in loghstash conf file.
- job status queue
- job metrics queue



