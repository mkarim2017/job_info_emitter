#/usr/bin/env python

'''
a sample daemonization script for the sqs listener
'''
import os
import sys
import json
import logging
import configparser
import requests
import urllib.request
import socket
from urllib.parse import urljoin
import time
import json
import time
import datetime
import hashlib
import traceback
import random
import datetime
from uuid import uuid4
from logger import ADESLogger
import argparse

SLEEP_TIME=60

prev_job_status = set()
prev_jobs = set()

host = urllib.request.urlopen('https://ifconfig.me').read().decode('utf8')
hostname = socket.gethostname()

logger = logging.getLogger('job_status_checker')
logger.setLevel(logging.INFO)

sh = logging.FileHandler('job_status_checker.log')
sh.setLevel(logging.INFO)

formatstr = '[%(asctime)s - %(name)s - %(levelname)s]  %(message)s'
formatter = logging.Formatter(formatstr)

sh.setFormatter(formatter)
logger.addHandler(sh)


class JobStatusProcessor():

    def get_hex_hash(self, data):
        return hashlib.md5(data.encode()).hexdigest()[0:8]

    def get_job_status(self):
        job_status_set = set()
        job_set = set()
        job_payload = {}
        process_ids = []
        processes = json.loads(self.getProcesses()).get("processes", [])
       
        for process in processes:
            process_info = process
            #logger.debug(json.dumps(process, indent=2))
            process_id = process["id"]
            jobs = json.loads(self.getJobList(process_id)).get("jobs", [])
        
            for job in jobs:
                logger.debug(json.dumps(job, indent=2))

                
                num = random.randint(1000, 10000)
                job_json = {} 
                priority = num%10
                job_id = job["jobID"]
                logger.debug("JOB_ID : {}".format(job_id))
                backend_info = json.loads(job['backend_info'])
                input_info = json.loads(job['inputs'])
                proc_id = job["procID"]
                metrics = json.loads(job["metrics"])
                logger.debug("BACKEND_INFO : {}".format(json.dumps(backend_info, indent=2)))
                logger.debug("INPUT_INFO : {}".format(json.dumps(input_info, indent=2)))
                logger.debug("PROCESS_INFO : {}".format(json.dumps(process_info, indent=2)))
                logger.debug("METRICS : {}".format(json.dumps(metrics, indent=2)))
                job_uid = "NA"
                
                try:
                    job_metadata = backend_info["api_response"]["metadata"]
                    job_spec = backend_info["api_response"]["spec"]
                    container_spec = job_spec["template"]["spec"]["containers"][0]
                    container_args = container_spec["args"]
                    container_command = container_spec["command"]
                    container_image = container_spec["image"]
                    job_name = job_metadata["name"]
                    job_namespace = job_metadata["namespace"]
                except Exception as err:
                    job_name = backend_info.get("pbs_job_id")
                    j_status = backend_info.get("status")
                

                '''
                job_data = json.loads(self.getStatus(process_id, job_id))
                job_statusInfo = job_data["statusInfo"]
                j_status = job_statusInfo["status"].strip().lower()
                job_id = job_statusInfo["jobID"]
                job_metrics_data = job_statusInfo.get("metrics", {})

                '''
                j_status = backend_info.get("status")
                job_metrics_data = metrics
                #logger.debug(json.dumps(job_metrics_data, indent=2))
                
                job_info = {}
                job_info['id'] = job_id
                job_info["ades_id"] = "NA" #job_data["ades_id"]
                endpoint_id = "NA" #job_data["ades_id"]
                job_info["api_version"] = "1.0" # job_data["api_version"]
                job_info["username"] = job["jobOwner"]
                job_info["job_type"] = proc_id #job_statusInfo.get("job_type", "UNKNOWN")
                job_info["time_queued"] = "{}Z".format(job["timeCreated"]).replace('+', '.')
                job_info["time_start"] = "{}Z".format(job_metrics_data.get("workflow", {}).get("time_start", "")).replace('+', '.')
                job_info["time_end"] = "{}Z".format(job_metrics_data.get("workflow", {}).get("time_end", "")).replace('+', '.')
                job_info["duration"] = "{}".format(job_metrics_data.get("workflow", {}).get("time_duration_seconds", ''))
                job_info["status"] = j_status
                hostname = "{}".format(job_metrics_data.get("workflow", {}).get("node", {}).get("hostname", "unknown"))


                job_info['execute_node'] = hostname
                job_id_hex = "{}-{}".format(self.get_hex_hash(job_id), self.get_hex_hash(j_status))

          
                job_status_set.add((job_id, j_status))
                job_set.add(job_id)
                        
                facts = {}
                facts['hysds_public_ip'] = host
                facts['ec2_instance_type'] = hostname
                facts['hysds_execute_node'] = hostname

                job_json = {}
                job_json['job_info'] = job_info
                job_json['container_image_name'] = process_info['owsContextURL'].split('/')[-1]
                job_json['container_image_url'] = process_info['owsContextURL']
                job_json['retry_count'] = 0
                job_json['facts'] = facts
                job_json['status'] = j_status
                job_json['name'] = job_id
                job_json['type'] = job_info["job_type"]
                job_json['username'] = job_info["username"] 
                job_json['priority'] = 1
                job_json['@version'] = '1'
                job_json['tag'] = job_info["ades_id"]
                job_json["task_id"] = job_id_hex
                job_json["command"] = {}
                job_json["params"] = {}
                job_json["context"] = {}
                job_json['container_image_id'] = process_info['owsContextURL'].split('/')[-1]
                event = {}
                event['traceback'] = 'unknown'

                payload = {}
                payload['resource'] = 'job'
                payload['payload_id'] = job_id

                delivery_info = {}
                delivery_info["redelivered"] = False
                delivery_info["routing_key"] = "NA"
                delivery_info["exchange"] = ""
                delivery_info["priority"] = 3
                #job_json["delivery_info"]: delivery_info

                container_mappings = {}
                container_mappings['$HOME/.netrc'] =  '/home/ops/.netrc'
                job_json['container_mappings'] = container_mappings
                #payload['@timestamp'] = job['timestamp']
                payload['status'] = j_status
                payload['tags'] = endpoint_id
                job_json['endpoint_id'] = job_info["ades_id"]
                payload['@version'] = '1'
                payload['dedup'] = True
                payload['job'] = job_json
                payload['type'] = process_info['id']
                uuid = str(uuid4())
                payload['uuid'] = uuid
                payload['payload_hash'] = hashlib.md5(json.dumps(payload).encode()).hexdigest()
                job_payload[job_id_hex] = payload
                break

            logger.debug(json.dumps(job_payload, indent=2))
        return job_status_set, job_set, job_payload 

    def submit_request(self, href, request_type, expected_response_code=200, payload_data=None, timeout=None):

        logger.debug('submit_request : href : {} request_type : {}'.format(href, request_type))
        headers = {'Content-type': 'application/json'}
        wps_server_url = urljoin(wps_server, href)
        logger.debug('wps_server_url : {}'.format(wps_server_url))
        if request_type.upper()=='GET':
            logger.debug('calling GET')
            if timeout:
                response = requests.get(wps_server_url, headers=headers, timeout=timeout)
            else:
                response = requests.get(wps_server_url, headers=headers)
            logger.debug(response.json())
        elif request_type.upper()=='POST':
            if payload_data:
                logger.debug('POST DATA : {}'.format(wps_server_url))
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                if timeout:
                    response = requests.post(wps_server_url, headers=headers, data={'proc' : payload_data}, timeout=timeout)
                else:
                    response = requests.post(wps_server_url, headers=headers, data={'proc' : payload_data})
            else:
                logger.info('POST: NO PAYLOAD_DATA')
                response = requests.post(wps_server_url, headers=headers)
        elif request_type.upper()=='DELETE':
            response = requests.delete(wps_server_url, headers=headers)
        else:
            raise Exception('Invalid Request Type : {}'.format(request_type))
         
        response.raise_for_status()
        logger.info('submit_request : {} status code: {}'.format(href, response.status_code))
        logger.debug(json.dumps(response.json(), indent=2))

        
        assert response.status_code == int(expected_response_code)

        return json.dumps(response.json())

    def getLandingPage(self):
        logger.debug('getLandingPage')
        href = ''	
        request_type = 'GET'
        return self.submit_request(href, request_type)

    def deployProcess(self, payload_data):
        href = 'processes'
        request_type = 'POST'
        return self.submit_request(href, request_type, 201, payload_data)

    def getProcessDescription(self, process_id):
        href = 'processes/{}'.format(process_id)
        request_type = 'GET'
        return self.submit_request(href, request_type)

    def undeployProcess(self, process_id):
        href = 'processes/{}'.format(process_id)
        request_type = 'DELETE'
        return self.submit_request(href, request_type)

    def getJobList(self, process_id):
        href = 'processes/{}/jobs'.format(process_id)
        request_type = 'GET'
        return self.submit_request(href, request_type)        
 
    def execute(self, process_id, payload_data):
        href = 'processes/{}/jobs'.format(process_id)
        request_type = 'POST'
        wps_server_url = urljoin(wps_server, href)
        headers = {'Content-type': 'application/json'}
        response = requests.post(wps_server_url, headers=headers, data=json.dumps(payload_data))
        response.raise_for_status()
        logger.debug('status code: {}'.format(response.status_code))
        logger.info(json.dumps(response.json(), indent=2))
        assert response.status_code == 201
        return json.dumps(response.json())

    def getStatus(self, process_id, job_id):
        href = 'processes/{}/jobs/{}'.format(process_id, job_id)
        request_type = 'GET'
        return self.submit_request(href, request_type)

    def dismissJob(self, process_id, job_id):
        href = 'processes/{}/jobs/{}'.format(process_id, job_id)
        request_type = 'DELETE'
        return self.submit_request(href, request_type)

    def getProcesses(self):
        href = 'processes'
        request_type = 'GET'
        return self.submit_request(href, request_type)

    def getResult(self, process_id, job_id):
        href = 'processes/{}/jobs/{}/result'.format(process_id, job_id) 
        request_type = 'GET'
        return self.submit_request(href, request_type)

    def getTempJobStatus(self):
        import random

        job_status = set()
        jobs = set()
        for i in range(1, 10):
            r = random.randint(0, 100)
            
            status = 'QUEUED'
            if r%5 == 0:
                status = 'FAILED'
            elif r%4 == 0:
                status = 'PASSED'
            elif r%3 == 0:
                status = 'RUNNING'
           
            if not r%7 == 0:
                job_name = 'Job{}'.format(i)
                job_status.add((job_name, status)) 
                jobs.add(job_name)
            
        return job_status, jobs


def file_based():

    global prev_job_status
    global prev_jobs

    JSP = JobStatusProcessor()
    #job_status, jobs = JSP.getTempJobStatus()
    job_status, jobs, job_payload = JSP.get_job_status()

    new_only_status = job_status - prev_job_status
    old_only_jobs = prev_jobs - jobs
    new_only_jobs = jobs - prev_jobs

    ''''
    delta = {}
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            data = json.load(f)
            for k in jobs.keys():
                if k not in data.keys():
                    logger.debug('Key {} not in {}'.format(k, data.keys()))
                    delta[k] = jobs[k]
                elif jobs[k] != data[k]:
                    logger.debug('{} != {}'.format(jobs[k], data[k]))
                    delta[k] = jobs[k]
            
    else:
        delta = jobs

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=4)
    
    logger.debug(json.dumps(delta, indent=2))
    '''

    prev_job_status = job_status
    prev_jobs = jobs


    return  new_only_jobs, old_only_jobs, new_only_status, job_payload  

def redis_based():
   pass


def main(server_ip="127.0.0.1", server_port="5000", log_file=None, endpoint_id="pbs"):
    global prev_job_status
    global prev_jobs
    global wps_server

    wps_server = "http://{}:{}".format(server_ip, server_port)
    log_file_json = "data.json"
    adesLogger = None

    if not log_file:
        log_file = os.path.join(os.getcwd(), "ADES_log_{}.log".format(endpoint_id))

    new_only_jobs, old_only_jobs, new_only_status, job_payload = file_based()

    new_jobs = {}
    for j in new_only_status:
        new_jobs[j[0]]=j[1]
    logger.info("job with new status : {}".format(new_jobs))

    logger.info("new_only_jobs : {}".format(new_only_jobs))
    logger.info("new_only_status : {}".format(new_only_status))

    adesLogger = None

    try:  
        adesLogger = ADESLogger.get_logger()
    except Exception as e:
        logger.info(str(e))
        logger.info('Instantiating ..')
        endpoint_id = "ades"
        adesLogger = ADESLogger(log_file) 

    if len(new_jobs.keys()) == 0:
        logger.info("No new job or new job status")

    for job in job_payload.keys():
        payload = job_payload[job]
        job_id = payload['job']['job_info']['id']
        if job_id not in new_jobs.keys():
            continue
       
        logger.info("New job status for job : {} : {}".format(job_id, new_jobs[job_id])) 
        payload_str = ''
        for k in payload.keys():
            if len(payload_str)>0:
                payload_str = payload_str+',{}:{}'.format(k,json.dumps(payload[k]))
            else:
                payload_str = '{}:{}'.format(k,json.dumps(payload[k])) 
        logger.info("\n\nWRITING log for job id : {}".format(job_id))
        adesLogger.log(job_id, json.dumps(job_payload[job]))
        #adesLogger.log(job, payload_str)
    '''
    for job in old_only:
        adesLogger.log(job, 'OFFLINE')
    '''
    #time.sleep(sleep_time)

if __name__ == '__main__':
    #main()
    parser = argparse.ArgumentParser("Tool to retrieve metrics information from ADES server")
    parser.add_argument("--output_log", required=False, help="Output Log File Name with Full Path")
    parser.add_argument("--server_ip", required=False, default="127.0.0.1", help="Flex Server IP Address")
    parser.add_argument("--server_port", required=False, default="5000", help="Flex Server Port")
    parser.add_argument("--config", required=False,
                        help="Optionally specify a config file with full path with other parameter info")
    args = parser.parse_args()
    
    server_ip = args.server_ip
    server_port = args.server_port
    output_log = args.output_log
    logger.info("{} : {} : {}".format(server_ip, server_port, output_log))
 
    while (1):
        if args.config:
            CONFIG_FILE_PATH = r'{}'.format(args.config)
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE_PATH)
            server_ip  = config["ADES_SERVER"].get("server_ip", server_ip)
            server_port  = config["ADES_SERVER"].get("server_port", server_port)
            output_log  = config["ADES_SERVER"].get("output_log", output_log)

        try:
            main(server_ip, server_port, output_log)
        except Exception as err:
            logger.info("Error : {}".format(str(err)))
            traceback.print_exc()
        print("{} sleeping for {} sec ...".format(datetime.datetime.now(), SLEEP_TIME))
        time.sleep(SLEEP_TIME)
