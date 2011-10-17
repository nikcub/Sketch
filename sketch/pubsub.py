#!/usr/bin/env python


"""
Pubsub - a pubsubhubbub client for Python and AppEngine

"""

"""
Protocol Suggestions:
* Send topic URL along with payload content so that we don't need to do a DB lookup, or so that we know what to unsubscribe for
* Or use a return code for this? let the hub know we don't want the content any more - MISSING
* we might change the callback URL, might do a lot of things, need to let it know we don't understand this request

"""
import base64
import logging
import simplejson
import datetime
import pickle
import hashlib, random, urllib

from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db

import sketch
from models import *

class PubSubException(Exception):
  pass

class PubSubClient(object):
    hub_url = None
    hub_credentials = None

    callback_host = ""
    callback_url = "/pubsub"
    callback_key = "key"
    callback_token = None

    def __init__(self, hub_url, hub_credentials = False, callback_url = None, callback_host = None, callback_token = None):
        self.hub_url = hub_url
        self.hub_credentials = hub_credentials
        if callback_url:
            self.callback_url = callback_url
        if callback_host:
            self.callback_host = callback_host
        if callback_token:
            self.callback_token = callback_token


    def _prepare_request(self, topic, callback, mode = "subscribe"):
        return {
            'hub.callback': callback,
            'hub.mode': mode,
            'hub.topic': topic,
            'hub.verify': 'async',
            # 'hub.verify_token': 'SEKRET_TOKENZ'
        }

    def _make_request(self, arg):
        headers = {}
        if self.hub_credentials:
            auth_string = "Basic " + base64.b64encode("%s:%s" % self.hub_credentials)
            headers['Authorization'] = auth_string

        headers['Connection'] = 'Close'

        # @TODO - make async http://code.google.com/appengine/docs/python/urlfetch/asynchronousrequests.html
        response = urlfetch.fetch(
            self.hub_url,
            payload = urllib.urlencode(arg),
            method = urlfetch.POST,
            headers = headers,
            deadline = 10
        )

        return response


    def get_callback_url(self, token = None):
        callback_url = self.callback_host + self.callback_url
        if token:
            callback_url += "?" + self.callback_key + "=" + token
        elif self.callback_token:
            callback_url += "?" + self.callback_key + "=" + self.callback_token
        return callback_url

    def subscribe(self, source):
        cb = self.get_callback_url(source.hub_verify_token)
        arg = self._prepare_request(source.url, cb)
        response = self._make_request(arg)
        if response.status_code == 204:
            source.set_status('subscribing')
            return True, response.content
        elif response.status_code == 202:
            source.set_status('deferred')
            return True, response.content
        else:
            source.set_status('error')
            return False, response.content

    def unsubscribe(self, source):
        cb = self.get_callback_url(source.hub_verify_token)
        arg = self._prepare_request(source.url, cb)
        response = self._make_request(arg)
        if response.status_code / 200 == 1:
            source.set_status('unsubscribing')
            return True, response.content
        else:
            return False, response.content



    def get_status(self, source):
        query_args = {
            "hub.mode": "retrieve",
            "hub.topic": source.url
        }
        headers = {}
        if self.hub_credentials:
            auth_string = "Basic " + base64.b64encode("%s:%s" % self.hub_credentials)
            headers['Authorization'] = auth_string

        headers['Connection'] = 'Close'

        req_url = self.hub_url + "?%s" % (urllib.urlencode(query_args))

        response = urlfetch.fetch(
            req_url,
            # payload = urllib.urlencode(subscribe_args),
            method = urlfetch.GET,
            headers = headers,
            deadline = 10
        )

        SourceMessage.create(source, "Made Status request to %s " % req_url)
        SourceMessage.create(source, "Status Response (%d): %s " % (response.status_code, response.content))

        return response.content



class PubSubHandler(sketch.BaseController):
    pubsub_callback_url = "%s/admin/hub/callback?key=%s"

    def post(self, arg):
        logging.info('PUBSUB: Started POST Controller')

        if not self.request.get('key'):
            return self.render_error(message = "Subscription not found: Key not specified.")

        src = Source.get_by_token(self.request.get('key'))

        if not src:
            logging.error("Got a subscription post that isn't stored")
            req_body = self.request.body
            feed_self = sketch.util.discover_feed_self(req_body)
            if not feed_self:
                logging.info("Could not find feed URL topic - have to manually unsubscribe from this one")
                return self.render_error(message = "Subscription not found")

            logging.info("Got self %s" % feed_self)
            hubs = sketch.util.discover_feed_hub(req_body)
            if not hubs:
                logging.info("Could not find feed hub - have to manually unsubscribe from this one")
                return self.render_error(message = "Subscription not found")

            for hub in hubs:
                src = Source(
                    key_name = feed_self,
                    hub_status = 'unknown',
                    hub_url = hub,
                    hub_verify_token = self.request.get('key')
                )
                src.put()
                t = PubSubClient(hub)
                hub_callback = self.pubsub_callback_url % (self.request.host_url, src.hub_verify_token)
                r, msg = t.subscribe(src, hub_callback, mode = "unsubscribe")

            self.response.set_status(200)
            return self.response.out.write('Unknown Subscription')

        has_error = False

        try:
            src.hub_status = 'subscribed'
            src.put()
            body = self.request.body.decode('UTF-8')
            logging.info('PUBSUB: GOT POST!')
            SourceMessage.create(src, "Received Post")
            # SourceMessage.create(src, self.request.body)
            # logging.info(self.request.body)

            data = sketch.feedparser.parse(self.request.body)

            if data.bozo:
                logging.error('Bozo feed data. %s: %r',
                    data.bozo_exception.__class__.__name__,
                    data.bozo_exception
                )
                if (hasattr(data.bozo_exception, 'getLineNumber') and hasattr(data.bozo_exception, 'getMessage')):
                    line = data.bozo_exception.getLineNumber()
                    logging.error('Line %d: %s', line, data.bozo_exception.getMessage())
                    segment = self.request.body.split('\n')[line-1]
                    logging.info('Body segment with error: %r', segment.decode('utf-8'))
                return self.response.set_status(500)

            update_list = []
            logging.info('Found %d entries', len(data.entries))
            for entry in data.entries:
                if hasattr(entry, 'content'):
                    # This is Atom.
                    entry_id = entry.id
                    title = entry.get('title', '')
                    content = entry.content[0].value
                    link = entry.get('link', '')

                else:
                    entry_id = (entry.get('id', '') or link or title or content)
                    title = entry.get('title', '')
                    content = entry.get('description', '')
                    link = entry.get('link', '')


                if hasattr(entry, 'updated_parsed'):
                    pubdate = datetime.datetime(*entry['updated_parsed'][:6])
                else:
                    pubdate = datetime.datetime.now()

                # shity pheedo link-rewriting
                if hasattr(entry, 'pheedo_origlink'):
                    link = entry.get('pheedo_origlink')

                try:
                    entry_raw = base64.b64encode(pickle.dumps(entry))
                except Exception, e:
                    logging.debug('PUBSUB ERROR: error pickling')

                logging.info('Found entry: %s: title="%s", link = "%s"', entry_id, title, link)
                # update_list.append(Post(


                if not src:
                    logging.error("ERROR: How do we not have a source at this point?")
                    src = Source.get_by_token(self.request.get('key'))

                try:
                    post = Post(
                        # key_name = 'key_' + hashlib.sha1(link + '\n' + entry_id).hexdigest(),
                        key_name = entry_id,
                        src = src.key()
                    )

                    post.title = title
                    post.content = content
                    post.post_type = 'post'
                    post.pubdate = pubdate
                    post.entry_raw = entry_raw
                    post.link = link

                    # )

                    r = post.put()
                    if r:
                        logging.info("POST SAVED")
                    else:
                        has_error = True
                except Exception, e:
                    logging.exception("PUBSUB ERROR: Could not insert entry")
                    logging.exception("%s: %s" % ('key_name', entry_id))
                    logging.exception("%s: %s" % ('src', src.key()))
                    logging.exception("%s: %s" % ('title', title))
                    logging.exception("%s: %s" % ('content', content))
                    logging.exception("%s: %s" % ('pubdate', pubdate))
                    logging.exception("%s: %s" % ('entry_raw', entry_raw))
                    logging.exception("%s: %s" % ('link', link))
                    logging.exception(e.message)
                    has_error = True

            # db.put(update_list)

        except Exception, e:
            logging.exception(e.message)
            logging.info('source is:')
            logging.exception(src)
            # logging.info(self.request.body)
            return self.render_error(message = "Exception Occured", code = 500)

        if not has_error:
            self.response.set_status(200)
            return self.response.out.write("Saved.")

        # code is temporarily 500 during dev so that the hub re-posts
        logging.exception('Fell to the end which means an error')
        return self.render_error(message = "Working out parsing. plz try again", code = 500)


    def get(self, arg):
        if not self.request.get('key'):
            return self.render_error(message = "Subscription not found: Key not specified.")

        src = Source.get_by_token(self.request.get('key'))

        if not src:
            return self.render_error(message = "Subscription not found")

        SourceMessage.create(src, "PUBSUB: Got callback for %s with key %s" % (src.url, self.request.get('key')))

        src_key = self.request.get('key', False)
        hub_mode = self.request.get('hub.mode', False)
        hub_challenge = self.request.get('hub.challenge', False)
        # hub_verify_token = self.request.get('hub.verify_token', False)
        hub_topic = self.request.get('hub.topic', False)
        hub_lease = self.request.get('hub.lease_seconds', False)

        if not src_key or not hub_mode or not hub_challenge or not hub_topic:
            msg = "Subscription not found: Not all hub parameters specified."
            SourceMessage.create(src, "PUBSUB: %s" % msg)
            return self.render_error(message = msg)

        if hub_mode == "subscribe":
            SourceMessage.create(src, "PUBSUB: %s" % "Got subscribe callback")
            src.set_status('subscribed')
            return self.render('pubsub.callback', {"key": hub_challenge})
        elif hub_mode == "unsubscribe":
            SourceMessage.create(src, "PUBSUB: %s" % "Got unsubscribe callback")
            src.set_status('unsubscribed')
            return self.render('pubsub.callback', {"key": hub_challenge})
        else:
            SourceMessage.create(src, "PUBSUB: %s" % "Got unsupported callback")
            return self.render_error(message = "Unsupported hub mode.")

