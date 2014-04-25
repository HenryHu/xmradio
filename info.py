import logging
logger = logging.getLogger('info')

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
