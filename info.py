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
