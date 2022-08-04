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
from uuid import uuid4
from logger import ADESLogger

CONFIG_FILER_PATH = r'endpoint_config.py'

config = configparser.ConfigParser()
config.read(CONFIG_FILER_PATH)

wps_server = config['ENDPOINT']['wps_server_url']
result_file = config['ENDPOINT']['result_file']
sleep_time = int(config['ENDPOINT']['sleep_in_secs'])
endpoint_id = config['ENDPOINT']['endpoint_id']

prev_job_status = set()
prev_jobs = set()

host = urllib.request.urlopen('https://ifconfig.me').read().decode('utf8')
hostname = socket.gethostname()

logger = logging.getLogger('sqs_listener')
logger.setLevel(logging.INFO)

sh = logging.FileHandler('soamc_sqs_client.log')
sh.setLevel(logging.INFO)

formatstr = '[%(asctime)s - %(name)s - %(levelname)s]  %(message)s'
formatter = logging.Formatter(formatstr)

sh.setFormatter(formatter)
logger.addHandler(sh)


class JobStatusProcessor():

    def get_hex_hash(self, data):
        return hashlib.md5(data.encode()).hexdigest()[0:8]

    def get_job_status(self):
        job_status = set()
        jobs = set()
        job_payload = {}
        process_ids = []
        processes = self.getProcesses()
       
        if processes:
            processes = json.loads(processes)

            for process in processes['processes']:
                process_ids.append(process['id'])
            print(process_ids)

            for pid in process_ids:
                joblist = self.getJobList(pid)

                if joblist:
                    joblist = json.loads(joblist)['jobs']
                    for j in joblist:
                        print(j.keys())
          
                        backend_info = json.loads(j['backend_info'])
                        process_info = backend_info['process']
                        input_info = json.loads(j['inputs'])
                        #print(json.dumps(input_info, indent=2))                  
                        #print(process_info.keys())
                        #print(json.dumps(j, indent=2))
                        #jobDesc = self.getStatus(pid,  j['jobID'])
                        #print('JOB STATUS')
                        #print(json.dumps(process_info, indent=2))
                        job_id = '{}-{}-{}'.format(endpoint_id, j['jobID'],j['timestamp'].replace(':', '-'))
                        job_id_hex = '{}-{}-{}-{}'.format(self.get_hex_hash(endpoint_id), self.get_hex_hash(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))[0:4],self.get_hex_hash(j['jobID']), self.get_hex_hash(j['timestamp'].replace(':', '-')))  
                        job_status.add((job_id_hex, j['status']))
                        jobs.add(job_id_hex)
                        job_info = {}
                        job_info['id'] = job_id
                        job_info['job_queue'] = 'factotum-job_worker-small'
                        job_info['execute_node'] = hostname
                        job_info['duration'] = 0
                        
                        facts = {}
                        facts['hysds_public_ip'] = host
                        facts['ec2_instance_type'] = hostname
                        facts['hysds_execute_node'] = hostname

                        job = {}
                        job['job_info'] = job_info
                        job['container_image_name'] = process_info['owsContextURL'].split('/')[-1]
                        job['container_image_url'] = process_info['owsContextURL']
                        job['retry_count'] = 0
                        job['facts'] = facts
                        #job['status'] = 'job-completed'
                        job['status'] = j['status']
                        job['name'] = job_id
                        job['type'] = process_info['id']
                        job['username'] = 'unknown'
                        job['priority'] = 1
                        job['@version'] = '1'
                        job['tag'] = endpoint_id
                        job["task_id"] = job_id_hex
                        job["command"] = {}
                        job["params"] = {}
                        job["context"] = {}
                        job['container_image_id'] = process_info['owsContextURL'].split('/')[-1]
                        event = {}
                        event['traceback'] = 'unknown'

                        payload = {}
                        #payload['_index'] = 'new_ades_sqs_test'
                        payload['resource'] = 'job'
                        payload['payload_id'] = job_id
                        
                        '''
                        payload['short_error'] = 'unknown'
                        payload['msg_details'] = 'unknown'
                        payload['traceback'] = 'unknown'
                        payload['error'] = 'unknown'
                        '''
                        delivery_info = {}
                        delivery_info["redelivered"] = False
                        delivery_info["routing_key"] = "factotum-job_worker-small"
                        delivery_info["exchange"] = ""
                        delivery_info["priority"] = 3
                        job["delivery_info"]: delivery_info

                        container_mappings = {}
                        container_mappings['$HOME/.netrc'] =  '/home/ops/.netrc'
                        job['container_mappings'] = container_mappings
                        payload['@timestamp'] = j['timestamp']
                        #payload['status'] = 'job-completed'
                        payload['status'] = j['status']
                        payload['tags'] = [process_info['keywords'], endpoint_id]
                        #payload['event'] = event
                        #payload['user_tags'] = [process_info['keywords'], endpoint_id]
                        #payload['dedup_job'] = 'unknown'
                        job['endpoint_id'] = endpoint_id
                        payload['@version'] = '1'
                        payload['dedup'] = True
                        payload['job'] = job
                        payload['type'] = process_info['id']
                        uuid = str(uuid4())
                        payload['uuid'] = uuid
                        payload['payload_hash'] = hashlib.md5(json.dumps(payload).encode()).hexdigest()
                        job_payload[job_id_hex] = payload

        return job_status, jobs, job_payload 

    def submit_request(self, href, request_type, expected_response_code=200, payload_data=None, timeout=None):

        logger.debug('submit_request : href : {} request_type : {}'.format(href, request_type))
        headers = {'Content-type': 'application/json'}
        wps_server_url = urljoin(wps_server, href)
        logger.info('wps_server_url : {}'.format(wps_server_url))
        if request_type.upper()=='GET':
            logger.debug('calling GET')
            if timeout:
                response = requests.get(wps_server_url, headers=headers, timeout=timeout)
            else:
                response = requests.get(wps_server_url, headers=headers)
            logger.debug(response.json())
        elif request_type.upper()=='POST':
            if payload_data:
                logger.info('POST DATA : {}'.format(wps_server_url))
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
        logger.info('status code: {}'.format(response.status_code))
        logger.info(json.dumps(response.json(), indent=2))

        
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
        logger.info('status code: {}'.format(response.status_code))
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
                    print('Key {} not in {}'.format(k, data.keys()))
                    delta[k] = jobs[k]
                elif jobs[k] != data[k]:
                    print('{} != {}'.format(jobs[k], data[k]))
                    delta[k] = jobs[k]
            
    else:
        delta = jobs

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=4)
    
    print(json.dumps(delta, indent=2))
    '''

    prev_job_status = job_status
    prev_jobs = jobs


    return  new_only_jobs, old_only_jobs, new_only_status, job_payload  

def redis_based():
   pass

def main():
    new_only_jobs, old_only_jobs, new_only_status, job_payload = file_based()

    adesLogger = None

    

    try:  
        adesLogger = ADESLogger.get_logger()
    except Exception as e:
        print(str(e))
        print('Instantiating ..')
        adesLogger = ADESLogger(os.getcwd(), endpoint_id)
        
    for job in job_payload.keys():
        payload = job_payload[job]
        payload_str = ''
        for k in payload.keys():
            if len(payload_str)>0:
                payload_str = payload_str+',{}:{}'.format(k,json.dumps(payload[k]))
            else:
                payload_str = '{}:{}'.format(k,json.dumps(payload[k])) 
        adesLogger.log(job, json.dumps(job_payload[job]))
        #adesLogger.log(job, payload_str)
    print(json.dumps(job_payload, indent=2))
    '''
    for job in old_only:
        adesLogger.log(job, 'OFFLINE')
    '''
    #time.sleep(sleep_time)

if __name__ == '__main__':
    while (1):
        main()
        time.sleep(sleep_time)

    
