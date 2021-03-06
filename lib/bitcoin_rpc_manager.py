'''
    Implements simple interface to bitcoind's RPC.
'''


import simplejson as json
from twisted.internet import defer

from stratum import settings

import time

import stratum.logger
log = stratum.logger.get_logger('bitcoin_rpc_manager')

from lib.bitcoin_rpc import BitcoinRPC


class BitcoinRPCManager(object):
    
    def __init__(self):
	self.conns = {}
	self.conns[0] = BitcoinRPC(settings.BITCOIN_TRUSTED_HOST,
                             settings.BITCOIN_TRUSTED_PORT,
                             settings.BITCOIN_TRUSTED_USER,
                             settings.BITCOIN_TRUSTED_PASSWORD)
	self.curr_conn = 0
	for x in range (1, 99):
	    if hasattr(settings, 'BITCOIN_TRUSTED_HOST_' + str(x)) and hasattr(settings, 'BITCOIN_TRUSTED_PORT_' + str(x)) and hasattr(settings, 'BITCOIN_TRUSTED_USER_' + str(x)) and hasattr(settings, 'BITCOIN_TRUSTED_PASSWORD_' + str(x)):
		self.conns[len(self.conns)] = BitcoinRPC(settings.__dict__['BITCOIN_TRUSTED_HOST_' + str(x)],
							settings.__dict__['BITCOIN_TRUSTED_PORT_' + str(x)],
							settings.__dict__['BITCOIN_TRUSTED_USER_' + str(x)],
							settings.__dict__['BITCOIN_TRUSTED_PASSWORD_' + str(x)])

    def next_connection(self):
	time.sleep(1)
	if len(self.conns) <= 1:
	    log.error("Problem with Pool 0 -- NO ALTERNATE POOLS!!!")
	    time.sleep(4)
	    return
	log.error("Problem with Pool %i Switching to Next!" % (self.curr_conn) )
	self.curr_conn = self.curr_conn + 1
	if self.curr_conn >= len(self.conns):
	    self.curr_conn = 0

    @defer.inlineCallbacks
    def check_height(self):
	while True:
	    try:
		resp = (yield self.conns[self.curr_conn]._call('getinfo', []))
		break
	    except:
		log.error("Check Height -- Pool %i Down!" % (self.curr_conn) )
		self.next_connection()
	curr_height = json.loads(resp)['result']['blocks']
	log.debug("Check Height -- Current Pool %i : %i" % (self.curr_conn,curr_height) )
	for i in self.conns:
	    if i == self.curr_conn:
		continue

	    try:
	    	resp = (yield self.conns[i]._call('getinfo', []))
	    except:
		log.error("Check Height -- Pool %i Down!" % (i,) )
		continue

	    height = json.loads(resp)['result']['blocks']
	    log.debug("Check Height -- Pool %i : %i" % (i,height) )
	    if height > curr_height:
		self.curr_conn = i
	defer.returnValue(True)

    def _call_raw(self, data):
	while True:
	    try:
		return self.conns[self.curr_conn]._call_raw(data)
	    except:
		self.next_connection()
           
    def _call(self, method, params):
	while True:
	    try:
		return self.conns[self.curr_conn]._call(method,params)
	    except:
		self.next_connection()

    def submitblock(self, block_hex):
	while True:
	    try:
		return self.conns[self.curr_conn].submitblock(block_hex)
	    except:
		self.next_connection()

    def getinfo(self):
	while True:
	    try:
		return self.conns[self.curr_conn].getinfo()
	    except:
		self.next_connection()
    
    def getblocktemplate(self):
	while True:
	    try:
		return self.conns[self.curr_conn].getblocktemplate()
	    except:
		self.next_connection()
 
    def prevhash(self):
	self.check_height()
	while True:
	    try:
		return self.conns[self.curr_conn].prevhash()
	    except:
		self.next_connection()
        
    def validateaddress(self, address):
	while True:
	    try:
		return self.conns[self.curr_conn].validateaddress(address)
	    except:
		self.next_connection()
	

