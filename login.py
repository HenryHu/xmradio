import cookielib, urllib2, urllib
from HTMLParser import HTMLParser
import logging
import json
import os

logger = logging.getLogger('login')
# logger.setLevel(logging.DEBUG)

login_url = "https://login.xiami.com/member/login"
login_post_url = "https://login.xiami.com/member/login"

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

def login(username, password):
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

    # ask for validation code
    if 'validate' in post_args:
        print "enter verification code from %s" % parser.validate_img
        img_content = urllib2.urlopen(parser.validate_img).read()
        with open('/tmp/validate.png', 'w') as imgf:
            imgf.write(img_content)
        os.system('xdg-open /tmp/validate.png')
        post_args['validate'] = raw_input('code: ')

    # do login
    login_ret = urllib2.urlopen(login_post_url, urllib.urlencode(post_args)).read()
    login_ret_parsed = json.loads(login_ret)
    logger.debug(login_ret_parsed)

    # check result
    if not login_ret_parsed['status']:
        print login_ret_parsed
        if 'message' in login_ret_parsed:
            print login_ret_parsed['message']
            raise Exception(login_ret_parsed['message'])
        else:
            raise Exception('login failed')
    logger.info('login ok')

if __name__ == '__main__':
    import init
    import config
    init.init()
    login(config.username, config.password)