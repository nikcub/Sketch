
import os, logging

import sketch
import oauth

from google.appengine.ext import db

class User(sketch.db.Model):
    username = db.StringProperty(required=True)
    name = db.StringProperty()
    email = db.EmailProperty()
    picture = db.StringProperty()
    password = db.StringProperty()
    admin = db.BooleanProperty(default = False)
    disabled = db.BooleanProperty(default = False)

    sess = db.StringProperty()

    tw_token = db.StringProperty()
    tw_secret = db.StringProperty()
    tw_username = db.StringProperty()
    tw_picture = db.StringProperty()
    tw_name = db.StringProperty()
    tw_id = db.IntegerProperty()

    fb_token = db.StringProperty()
    fb_secret = db.StringProperty()
    fb_username = db.StringProperty()
    fb_picture = db.StringProperty()

    @property
    def id(self):
        return self.key()
        
    @property
    def k(self):
        return self.key()

    @property
    def admins(self):
        return self.admin is True

    @classmethod
    def createa_new(self, **kwargs):
        kwargs['username'] = username
        kwargs['key_name'] = username

        kwargs['passowrd'] = password

        def trans():
            if cls.get_by_key_name('name') is not None:
                return None

            usr = cls(**kwargs)
            usr.put()
            return usr

        return db.run_in_transaction(trans)

    @classmethod
    def get_login(self, username, password):
        query = db.GqlQuery("SELECT * from User where username = :1 and password = :2", username, password)
        re = query.fetch(1)
        if re:
            return re[0]
        return False

    @classmethod
    def create(self, username, email, password, image = None):
        user = User(
            username = username,
            email = email,
            image = image,
            password = password
        )
        return user.put()

    @classmethod
    def fetch(self, username = None, email = None, tw_username = None, fb_username = None):
        query_field = None
        if email:
            query_field = "email"
            query_value = email
        if username:
            query_field = "username"
            query_value = username
        if tw_username:
            query_field = "tw_username"
            query_value = tw_username
        if fb_username:
            query_field = "fb_username"
            query_value = fb_username
        if not query_field:
            raise ModelException, "Require one of email, username or linked account to query user"

        query = db.GqlQuery("SELECT * from User where %s = :1" % query_field, query_value)
        result = query.fetch(1)

        if result:
            return result[0]
        else:
            return False

    def log(self, action = "login", message = None):
        if action not in ["login", "logout", "adminloginas", "link_twitter", "link_facebook"]:
            raise Exception("Not a valid log action %s" % action)

        ua = os.environ.get('HTTP_USER_AGENT', '')
        ip = os.environ.get('REMOTE_ADDR', '')
        re = os.environ.get('HTTP_REFERER', '')

        ua = UserActivity(
            username = self.key(),
            action = action,
            ua = ua,
            ip = ip,
            message = message,
        )
        ua.put()

class UserActivity(sketch.db.Model):
    username = db.ReferenceProperty(User, collection_name="activity")
    action = db.StringProperty(choices = set(["login", "logout", "link_twitter", "link_facebook"]))
    ip = db.StringProperty()
    ua = db.StringProperty()
    message = db.StringProperty()

    @classmethod
    def create(self, user, action="login", message = None):
        ua = UserActivity(
        )



class LoginHandler(sketch.BaseController):
    tw_consumer_key = "CdkFQYSXbud586od8N0Q"
    tw_consumer_secret = "5e9b3a9wtXwx8ClHhHEKw5xTMjSKiNxLY9V3bm7ko"
    tw_callback_url = "%s/login/twitter/callback"

    def create_user(self, profile):
        return True

    def twitter_login(self, popup = False):
        callback_url = self.tw_callback_url % self.request.host_url
        if popup:
          callback_url += "?popup=1"
        client = oauth.TwitterClient(
          self.tw_consumer_key,
          self.tw_consumer_secret,
          callback_url
          )
        auth_url = client.get_authorization_url()
        logging.info("Twitter redir URL: %s" % auth_url)
        # self.redirect(client.get_authorization_url())
        return auth_url

    def twitter_callback(self):
        client = oauth.TwitterClient(
          self.tw_consumer_key,
          self.tw_consumer_secret,
          self.tw_callback_url % self.request.host_url
        )
        auth_token = self.request.get("oauth_token")
        auth_verifier = self.request.get("oauth_verifier")
        user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)
        return user_info

    def twitter_test(self):
        client = oauth.TwitterClient(
          self.tw_consumer_key,
          self.tw_consumer_secret,
          self.tw_callback_url % self.request.host_url
        )
        t = self.user.tw_token
        s = self.user.tw_secret
        return client.get_friends(t, s)

    def get(self, action, service = None):
        popup = self.request.get('popup', False)
        if action == "twitter":
            url = self.twitter_login(popup)
            return self.redirect(url)
        elif action == "test":
            test = self.twitter_test()
            return self.render('json', test)
        elif action =="callback" and service == "twitter":
            if not self.request.get("oauth_token"):
                return self.render_error(message = "err")

            content = self.twitter_callback()

            if not content.has_key('username'):
                return self.redirect('/index?loginerror')

            user = User.fetch(tw_username = content['username'])

            if not user:
                user = User(
                    username = content['username'],
                    password = sketch.util.generate_password(),
                    tw_username = content['username'],
                    picture = content['picture'],
                    tw_picture = content['picture'],
                    name = content['name'],
                    tw_secret = content['secret'],
                    tw_token = content['token'],
                    tw_id = content['id']
                )
                r = user.put()

            self.session['user'] = user.username
            self.session['key'] = str(user.key())
            self.session['auth'] = True
            
            user.sess = self.session.sid
            user.log("login")
            r = user.put()
            
            if popup:
              return self.render('login_popup', {})
            return self.redirect('/?existing_login')

        elif action == "clear":
            self.session.destroy()
            self.set_message('Logged Out')
            return self.redirect('/?loggedout')
        else:
            return self.render('index', {"error": "not implemented"})

    def post(self, action = None):
        logging.info("got action %s" % action)

        if not action:
            self.set_msg("Invalid")
            return self.redirect_back()

        if action == "local":
            username = self.request.get("username", "")
            password = self.request.get("password", "")
            if not username or not password:
                self.set_msg("Please enter a username or password")
                return self.redirect('/?login')
            user = User.get_login(username, password)
            if user:
                self.session['auth'] = True
                self.session['username'] = user.username
                self.session['userid'] = str(user.id)
                logging.info("SESSION")
                logging.info(self.session['username'])
                logging.info(self.session['userid'])
                logging.info(self.session['auth'])
                logging.info(self.session)
                self.set_message('logged in')
                return self.redirect('/')
            else:
                self.set_message('bad username or password')
                return self.redirect('/?login')


        self.set_message('whaaa?')
        self.redirect_back()


def gen_salt(length=10):
        """Generates a random string of SALT_CHARS with specified ``length``.

        :param length:
                Length of the salt.
        :returns:
                A random salt.
        """
        if length <= 0:
                raise ValueError('requested salt of length <= 0')

        return ''.join(choice(SALT_CHARS) for i in xrange(length))


def gen_pwhash(password):
        """Returns the password encrypted in sha1 format with a random salt.

        :param password:
                Password to e hashed and formatted.
        :returns:
                A hashed and formatted password.
        """
        if isinstance(password, unicode):
                password = password.encode('utf-8')

        salt = gen_salt()
        h = sha1()
        h.update(salt)
        h.update(password)
        return 'sha1$%s$%s' % (salt, h.hexdigest())


def check_password(pwhash, password):
        """Checks a password against a given hash value. Since  many systems save
        md5 passwords with no salt and it's technically impossible to convert this
        to a sha hash with a salt we use this to be able to check for legacy plain
        or salted md5 passwords as well as salted sha passwords::

                plain$$default

        md5 passwords without salt::

                md5$$c21f969b5f03d33d43e04f8f136e7682

        md5 passwords with salt::

                md5$123456$7faa731e3365037d264ae6c2e3c7697e

        sha passwords::

                sha1$123456$118083bd04c79ab51944a9ef863efcd9c048dd9a

        >>> check_password('plain$$default', 'default')
        True
        >>> check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
        True
        >>> check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'wrong')
        False
        >>> check_password('md5$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', u'example')
        True
        >>> check_password('sha1$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
        False
        >>> check_password('md42$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', 'example')
        False

        :param pwhash:
                Hash to be checked.
        :param password:
                Password to be checked.
        :returns:
                True if the password is valid, False otherwise.
        """
        if not pwhash or not password:
                return False

        if isinstance(password, unicode):
                password = password.encode('utf-8')

        if pwhash.count('$') < 2:
                return False

        method, salt, hashval = pwhash.split('$', 2)

        if method == 'plain':
                return hashval == password
        elif method == 'md5':
                h = md5()
        elif method == 'sha1':
                h = sha1()
        else:
                return False

        h.update(salt)
        h.update(password)
        return h.hexdigest() == hashval
