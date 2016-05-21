import cookielib, urllib2, urllib
from HTMLParser import HTMLParser
import logging
import json
import os

logger = logging.getLogger('login')
# logger.setLevel(logging.DEBUG)

login_url = "https://login.xiami.com/member/login"
login_post_url = "https://login.xiami.com/member/login"
img_path = "/tmp/validate.png"

class LoginPageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_login_form = False
        self.attrs = {}
        self.validate_img = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            if 'action' in attrs and attrs['action'] == login_post_url:
                logger.debug('hit login form')
                self.in_login_form = True
        if self.in_login_form:
            if tag == 'input':
                if 'name' in attrs:
                    if 'value' in attrs:
                        value = attrs['value']
                    else:
                        value = ''
                    self.attrs[attrs['name']] = value
            elif tag == 'img':
                if 'id' in attrs and attrs['id'] == 'code':
                    logger.info("verification code at %s" % attrs['src'])
                    self.validate_img = attrs['src']

    def handle_endtag(self, tag):
        if tag == 'form':
            if self.in_login_form:
                self.in_login_form = False

    def handle_data(self, data):
        pass

def login(state, username, password):
    login_page = urllib2.urlopen(login_url).read()

    # parse login page, find login arguments
    parser = LoginPageParser()
    parser.feed(login_page)
    post_args = parser.attrs
    if not post_args:
        raise Exception("fail to find login form")

    # fill in the form
    post_args['email'] = username
    post_args['password'] = password

    if 'validate' in post_args:
        img_content = urllib2.urlopen(parser.validate_img).read()
        return (False, post_args, img_content)

    login_with_code(state, post_args, None)
    return (True,)

def login_with_code(state, post_args, code):
    if code is not None:
        post_args['validate'] = code

    # do login
    login_ret = urllib2.urlopen(login_post_url, urllib.urlencode(post_args)).read()
    login_ret_parsed = json.loads(login_ret)
    logger.debug(login_ret_parsed)

    # check result
    if not login_ret_parsed['status']:
        logger.debug(login_ret_parsed)
        if 'message' in login_ret_parsed:
            logger.debug(login_ret_parsed['message'])
            raise Exception(login_ret_parsed['message'])
        else:
            raise Exception('login failed')

    state['user_nick'] = login_ret_parsed['data']['nick_name']
    state['user_id'] = login_ret_parsed['data']['user_id']

    if 'jumpurl' in login_ret_parsed and login_ret_parsed['jumpurl']:
        jumpurl = login_ret_parsed['jumpurl']
        jump_page = urllib2.urlopen(jumpurl).read()

    logger.info('login ok')

def login_console(state, username, password):
    ret = login(state, username, password)
    if not ret[0]:
        # ask for validation code
        print("enter verification code at %s" % img_path)
        with open(img_path, 'w') as imgf:
            imgf.write(ret[2])
        os.system('xdg-open %s' % img_path)
        code = raw_input('code: ')
        login_with_code(state, ret[1], code)

if __name__ == '__main__':
    import init
    import config
    state = init.init()
    login_console(state, config.username, config.password)
