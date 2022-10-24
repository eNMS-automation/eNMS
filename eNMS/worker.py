from dramatiq.brokers.redis import RedisBroker
from dramatiq import set_broker
from os import getenv

from eNMS.variables import vs

# There's a compatibility issue if decode_responses=True in the redis config.
broker = RedisBroker(host=getenv("REDIS_ADDR"), **{k:v for k,v in vs.settings['redis']['config'].items() if k != 'decode_responses'})
set_broker(broker)