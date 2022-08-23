'''
Check ADES Metrics
'''


import os
import sys
import json
import logging
import configparser
import requests
import argparse
import urllib
from urllib.parse import urljoin
import time
import traceback
import requests
import socket
import datetime
import hashlib
from uuid import uuid4
from logger import ADESLogger
import random
import traceback

logger = logging.getLogger('sqs_listener')
logger.setLevel(logging.INFO)

sh = logging.FileHandler('soamc_sqs_client.log')
sh.setLevel(logging.INFO)

formatstr = '[%(asctime)s - %(name)s - %(levelname)s]  %(message)s'
formatter = logging.Formatter(formatstr)

sh.setFormatter(formatter)
logger.addHandler(sh)

wps_server = "http://localhost:5000"
job_status_map = {"successful" : "job-completed", "accepted": "job-queued", "failed": "job-failed", "running": "job-started"}

hostname = socket. gethostname()
host = socket.gethostbyname(hostname)

SLEEP_TIME=60

prev_job_status = set()
prev_jobs = set()


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


class JobInfoProcessor():
    def get_hex_hash(self, data):
        return hashlib.md5(data.encode()).hexdigest()[0:8]

    def create_node_info(self, metrics_data):
        num = random.randint(11, 100)
        node = {}
        node["cores"] = metrics_data["cores_allowed"]
        node["memory"] = metrics_data["max_parallel_ram_megabytes"] * metrics_data["max_parallel_tasks"]
        node["disk_space_free"] = random.randint(11, 101)
        node["ip_address"] = host
        node["hostname"] = hostname
        node["blob"] =  json.dumps(metrics_data)
        return node


    def submit_request(self, href, request_type, expected_response_code=200, payload_data=None, timeout=None):

        logger.debug("submit_request : href : {} request_type : {}".format(href, request_type))
        headers = {'Content-type': 'application/json'}
        wps_server_url = urljoin(wps_server, href)
        logger.info("wps_server_url : {}".format(wps_server_url))
        if request_type.upper()=="GET":
            logger.debug("calling GET")
            if timeout:
                response = requests.get(wps_server_url, headers=headers, timeout=timeout)
            else:
                response = requests.get(wps_server_url, headers=headers)
            logger.debug(response.json())
        elif request_type.upper()=="POST":
            if payload_data:
                logger.info("POST DATA : {}".format(wps_server_url))
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                if timeout:
                    response = requests.post(wps_server_url, headers=headers, data={"proc" : payload_data}, timeout=timeout)
                else:
                    response = requests.post(wps_server_url, headers=headers, data={"proc" : payload_data})
            else:
                logger.info("POST: NO PAYLOAD_DATA")
                response = requests.post(wps_server_url, headers=headers)
        elif request_type.upper()=="DELETE":
            response = requests.delete(wps_server_url, headers=headers)
        else:
            raise Exception("Invalid Request Type : {}".format(request_type))
         
        response.raise_for_status()
        logger.info("status code: {}".format(response.status_code))
        logger.info(json.dumps(response.json(), indent=2))

        
        assert response.status_code == int(expected_response_code)

        return json.dumps(response.json())

    def getLandingPage(self):
        logger.debug("getLandingPage")
        href = ""	
        request_type = "GET"
        return json.loads(self.submit_request(href, request_type))

    def deployProcess(self, payload_data):
        href = "processes"
        request_type = "POST"
        return self.submit_request(href, request_type, 201, payload_data)

    def getProcessDescription(self, process_id):
        href = "processes/{}".format(process_id)
        request_type = "GET"
        return self.submit_request(href, request_type)

    def undeployProcess(self, process_id):
        href = "processes/{}".format(process_id)
        request_type = "DELETE"
        return self.submit_request(href, request_type)

    def getJobList(self, process_id):
        href = "processes/{}/jobs".format(process_id)
        request_type = "GET"
        return self.submit_request(href, request_type)        
 
    def execute(self, process_id, payload_data):
        href = "processes/{}/jobs".format(process_id)
        request_type = "POST"
        wps_server_url = urljoin(wps_server, href)
        headers = {'Content-type': 'application/json'}
        response = requests.post(wps_server_url, headers=headers, data=json.dumps(payload_data))
        response.raise_for_status()
        logger.info("status code: {}".format(response.status_code))
        logger.info(json.dumps(response.json(), indent=2))
        assert response.status_code == 201
        return json.dumps(response.json())

    def getStatus(self, process_id, job_id):
        href = "processes/{}/jobs/{}".format(process_id, job_id)
        request_type = "GET"
        return self.submit_request(href, request_type)

    def dismissJob(self, process_id, job_id):
        href = "processes/{}/jobs/{}".format(process_id, job_id)
        request_type = "DELETE"
        return self.submit_request(href, request_type)

    def getProcesses(self):
        href = "processes"
        request_type = "GET"
        return self.submit_request(href, request_type)

    def getResult(self, process_id, job_id):
        href = "processes/{}/jobs/{}/result".format(process_id, job_id) 
        request_type = "GET"
        return self.submit_request(href, request_type)

    def get_payload_data(self, job_data):
        job_metrics = {}
        job_info = {}
        job_json = {}

        num = random.randint(1000, 10000)

        job_statusInfo = job_data["statusInfo"]
        job_status = job_statusInfo["status"].strip().lower()
        job_id = job_statusInfo["jobID"]
        job_metrics_data = job_statusInfo["metrics"]
        job_step_data = job_metrics_data.get("processes", [])
        priority = num%10

        job_info["ades_id"] = job_data["ades_id"]
        job_info["api_version"] = job_data["api_version"]
        job_info["username"] = job_statusInfo["username"]

        job_info["time_queued"] = "{}Z".format(job_statusInfo["time_queued"])
        job_info["time_start"] = "{}Z".format(job_metrics_data.get("workflow", {}).get("time_start", ""))
        job_info["time_end"] = "{}Z".format(job_metrics_data.get("workflow", {}).get("time_end"))
        job_info["duration"] = "{}".format(job_metrics_data.get("workflow", {}).get("time_duration_seconds"))
        job_info["status"] = job_status_map[job_status]
        #job_info["job_queue"] = "factotum-job_worker-large"
        #job_info["public_ip"] =  host # "10.1.{}.{}".format(random.randint(1, 10), random.randint(11, 101))
        #job_info['execute_node'] = hostname
        #job_info["priority"] = priority
        
        job_info["metrics"] = job_metrics_data
        job_json["job_info"] = job_info
        job_json["priority"] = priority
  

        payload = {}
        payload['resource'] = 'job'
        payload['payload_id'] = job_id
        payload['@version'] = '1'
        payload['dedup'] = True
        payload['job'] = job_json
        payload['status'] =  job_status_map[job_status]

        return payload

    def get_job_metrics_from_log(self, log_file_json):
        num = random.randint(1000, 10000)

        job_payload = {}
        total_job_data = []
        total_job_metrics = {}

        with open(log_file_json, "r") as infile:
            job_status_data = json.load(infile)

        for j in job_status_data.keys():
            job_json = {}

            job_data = job_status_data[j]
            print(json.dumps(job_data, indent=2))
            job_metrics_data = job_data["statusInfo"]["metrics"]
            payload = self.get_payload_data(job_data)
            uuid = str(uuid4())
            #payload['uuid'] = uuid
            payload['payload_hash'] = hashlib.md5(json.dumps(payload).encode()).hexdigest()

            print(json.dumps(payload, indent=2))
            job_payload[payload['payload_hash']] = payload
            total_job_data.append(payload)

        total_job_metrics["job"] = total_job_data
        return job_payload, total_job_metrics
   
        
    def get_job_metrics(self):
        num = random.randint(1000, 10000)

        job_payload = {}
        total_job_data = []
        total_job_metrics = {}

        job_status_set = set()
        jobs_set = set()


        processes = json.loads(self.getProcesses()).get("processes", [])
        for process in processes:
            process_info = process
            #print(json.dumps(process, indent=2))
            process_id = process["id"]
            jobs = json.loads(self.getJobList(process_id)).get("jobs", [])
        
            for job in jobs:
                job_json = {} 
                priority = num%10
                job_id = job["jobID"]
                backend_info = json.loads(job['backend_info'])
                input_info = json.loads(job['inputs'])
                proc_id = job["procID"]
                print("BACKEND_INFO : {}".format(json.dumps(backend_info, indent=2)))
                print("INPUT_INFO : {}".format(json.dumps(input_info, indent=2)))
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
                    #job_uid = job_metadata["uid"]
                    job_creation_time = job_metadata["creationTimestamp"]
                    #job_id_new = '{}-{}-{}'.format(job_namespace, job_id, job_name, job_creation_time.replace(':', '-'))
                    #job_id_hex = '{}-{}-{}-{}'.format(self.get_hex_hash(job_namespace), self.get_hex_hash(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))[0:4],self.get_hex_hash(job_name), self.get_hex_hash(job_creation_time.replace(':', '-')))  
                except Exception as err:
                    job_name = backend_info.get("pbs_job_id")
                    job_status = backend_info.get("status")

                job_data = json.loads(self.getStatus(process_id, job_id))
                print("START OF JOB STATUS")
                print(json.dumps(job_data, indent=2))
                print("END OF JOB STATUS")
                job["ades_id"] = job_data["ades_id"]
                job["api_version"] = job_data["api_version"]

                job_statusInfo = job_data["statusInfo"]
                job["username"] = job_statusInfo["username"]
                job_status = job_statusInfo["status"].strip().lower()
                job_status_set.add((job_statusInfo["jobID"], job_status))
                jobs_set.add(job_statusInfo["jobID"])

                print("job_status : {}".format(job_status))
                if job_status=="successful" or job_status=="failed":
                    exit_code=1
                    if job_status == "successful":
                        exit_code=0
                    job_metrics_data=job_statusInfo["metrics"]

                    payload = self.get_payload_data(job_data)

                    #payload['uuid'] = job_uid
                    payload['payload_hash'] = hashlib.md5(json.dumps(payload).encode()).hexdigest()

                    print(json.dumps(payload, indent=2))
                    job_payload[payload['payload_hash']] = payload
                    total_job_data.append(payload)
                
        total_job_metrics["job"] = total_job_data
        return job_payload, total_job_metrics, job_status_set, jobs_set


def main():

    global prev_job_status
    global prev_jobs

    log_file_json = "data.json"
    adesLogger = None

    JIP = JobInfoProcessor()
    print(json.dumps(JIP.getLandingPage(), indent=2))
    #exit(0)
    job_payload, job_metrics, job_status_set, jobs_set = JIP.get_job_metrics()
    #job_payload, job_metrics = JIP.get_job_metrics_from_log(log_file_json)

    print("main : job_payload type : {}".format(type(job_payload)))

   
    new_only_status = job_status_set - prev_job_status
    print("new_only_status : {}".format(new_only_status))
    new_jobs = []
    for j in new_only_status:
        new_jobs.append(j[0])
    print("new_jobs : {}".format(new_jobs))

    old_only_jobs = prev_jobs - jobs_set
    new_only_jobs = jobs_set - prev_jobs

    prev_job_status = job_status_set
    prev_jobs = jobs_set

    print("new_only_jobs : {}".format(new_only_jobs))

    try:  
        adesLogger = ADESLogger.get_logger()
    except Exception as e:
        print(str(e))
        print('Instantiating ..')
        endpoint_id = "ades"
        adesLogger = ADESLogger(os.getcwd(), endpoint_id)
        
    for job in job_payload.keys():
        payload = job_payload[job]
        job_id = payload['payload_id'] 
        if job_id not in new_jobs:
            print("{} NOT in {}".format(job_id, new_jobs))
            continue

        payload_str = ''
        for k in payload.keys():
            if len(payload_str)>0:
                payload_str = payload_str+',{}:{}'.format(k,json.dumps(payload[k]))
            else:
                payload_str = '{}:{}'.format(k,json.dumps(payload[k])) 
        adesLogger.log(job, json.dumps(job_payload[job]))
        #adesLogger.log(job, payload_str)
    print(json.dumps(job_payload, indent=2))

if __name__ == '__main__':
    #main()
    while (1):
        try:
            main()
        except Exception as err:
            print("Error : {}".format(str(err)))
            traceback.print_exc()
        time.sleep(SLEEP_TIME)
