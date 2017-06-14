"""
This file holds various configuration options used for all of the examples.

You will need to change the values below to match your test account.
"""
import os
import sys
# Use the fedex directory included in the downloaded package instead of
# any globally installed versions.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fedex.config import FedexConfig

class fedex_config():
    '''
     This class creates an object that holds the fedex account details
    '''
    
    def __init__(self,key = None,password = None,account_number = None,meter_number = None,freight_account_number=None,use_test_server=True):
            self.CONFIG_OBJ = FedexConfig(key=key,
                         password=password,
                         account_number=account_number,
                         meter_number=meter_number,
                         freight_account_number=freight_account_number,
                         use_test_server=use_test_server)
                    