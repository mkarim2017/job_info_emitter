"""
Generic ADES Logging module to emit log in format
     <timestamp>, <host>, <source_type>, <endpoint_id>, <key>, <value>
"""

import os
import logging
import urllib.request
import time
import socket

class ADESLogger:
    __ades_logger = None
    
    def __init__(self, log_file):
        """
        Configures a logger to write log lines to /file_dir/name.adesEmmitter.log with
        format <timestamp>, <host>, <source_type>, <endpoint_id>, <metric_key>, <metric_value>

        Args:
          log_file (str): Log file name with full path"
        """

        if ADESLogger.__ades_logger != None:
            raise Exception("ADESLogger already existed. Please use ADESLogger.get_ades_logger() instead")
    
        self._logger = ADESLogger.__get_logger(log_file)
 
        # restrict the instantiation of a class to one "single" instance
        ADESLogger.__ades_logger = self
        
    @staticmethod
    def __get_logger(log_file):
        """
        Configures Python logger
        """
        # get public ip address
        #host = urllib.request.urlopen('https://ifconfig.me').read().decode('utf8')
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)

        file_dir, file_name = os.path.split(log_file)
        if not file_dir or len(file_dir) == 0:
            file_dir = os.getcwd()

        if not file_name or len(file_name) == 0:
            file_name = "ADESMetricsEmmitter_"+hostname.split('.')[0]+ ".log"


        # if the directory containing the output log file doesn't exist,
        # create one
        os.makedirs(file_dir, exist_ok = True)
        file_path = os.path.join(file_dir, file_name)

        # define the log format. By default, python logging module already
        # provides timestamp when logging

        '''
        log_format = ("\'%(asctime)s.%(msecs)03d\',"
                      "\'" + hostname + "\',"
                      "\'" + host + "\',"
                      "\'" + endpoint_id + "\'," 
                      "%(metric_key)s,"
                      "%(metric_value)s")
        '''

        log_format = ("%(metric_key)s+++"
                      "%(metric_value)s")
        datefmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(log_format, datefmt=datefmt)

        # By default, ADES use INFO level for logging
        level = logging.INFO
        
        # specify where to send the log, and make sure to use formatter to format it
        adesEmmitter_handler = logging.FileHandler(filename = file_path)
        adesEmmitter_handler.setLevel(level)
        adesEmmitter_handler.setFormatter(formatter)

        # configure SDS Watch Logger with the above handler
        logger = logging.getLogger("adesEmmitter")
        logger.setLevel(level)
        logger.addHandler(adesEmmitter_handler)
        logging.Formatter.converter = time.gmtime
        print("created logger : {}".format(adesEmmitter_handler.baseFilename))
        return logger
        

    def log(self, metric_key, metric_value):
        """
        Writes a log line with given format to the file created in configuration methods.
        
        Args:
          metric_key (str or number): value of key token
          metric_value (str or number): value of value token

        Note:
          use double quote to allow comma within metric_value
        """
        self._logger.info('', extra = {"metric_key" : metric_key, "metric_value" : metric_value})
        
    @staticmethod
    def get_logger():
        """
        Returns a ADESLogger instance if one already existed
        """
        if ADESLogger.__ades_logger == None:
            raise Exception("ADESLogger hasn't existed. Please instantiate it first !")
        return ADESLogger.__ades_logger
