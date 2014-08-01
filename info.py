import logging
import urllib2
import json
import time

is_vip_url = "http://www.xiami.com/vip/role"
stat_url_temp = "http://www.xiami.com/count/playstat?type=%d&vip_role=%d&song_id=%s"
record_play_url_temp = "http://www.xiami.com/count/playrecord?object=%s&sid=%s&object_name=%s&ishq=%d&t=%d"
record_play_simple_url_temp = "http://www.xiami.com/count/playrecord?sid=%s&type=%s&ishq=%d"

logger = logging.getLogger('info')

STAT_BEGIN = 0
STAT_NEAREND = 2
STAT_END = 3

def update_state(state, config_node):
    for child in config_node:
        if child.tag == 'nick_name':
            state['user_nick'] = child.text
        elif child.tag == 'user_id':
            state['user_id'] = child.text
        elif child.tag == 'vip':
            state['vip'] = child.text
        elif child.tag == 'vip_role':
            state['vip_role'] = child.text

def get_xiamitoken(state):
    for cookie in state['cookiejar']:
        if cookie.name == '_xiamitoken':
            logger.debug('_xiamitoken = %s' % cookie.value)
            return cookie.value
    raise Exception("fail to find xiami token!")

def authenticated(state):
    for cookie in state['cookiejar']:
        if cookie.name == 'member_auth':
            logger.debug('already authenticated')
            return True
    logger.debug('not authenticated')
    return False

def is_vip(state):
    if 'vip' in state:
        return state['vip']
    isvip_resp = urllib2.urlopen(is_vip_url).read()
    isvip_parsed = json.loads(isvip_resp)
    if not 'status' in isvip_parsed or isvip_parsed['status'] != 1:
        if 'message' in isvip_parsed:
            raise Exception(u"fail to check vip status: %s" % isvip_parsed['message'])
        else:
            raise Exception("fail to check vip status")
    result = isvip_parsed['data']['vip'] == 1
    state['vip'] = result
    return result

def add_stat(state, pos, song_id):
    stat_url = stat_url_temp % (pos, 1 if is_vip(state) else 0, song_id)
    urllib2.urlopen(stat_url).read()

def record_play(state, song_id, object_name, is_hq, play_type):
    hq_arg = 1 if is_hq else 0
    if object_name:
        record_play_url = record_play_url_temp % (
                song_id, song_id, object_name, hq_arg, int(time.time() * 1000))
    else:
        record_play_url = record_play_simple_url_temp % (
                song_id, play_type, hq_arg)
    urllib2.urlopen(record_play_url).read()

