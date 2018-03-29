#!/usr/bin/python
"""
One-shot eval....

Running as back process using App Engine queues
"""

import os
import sys
import traceback
import time
import StringIO
import json
import logging

import webapp2
from google.appengine.ext import db
from google.appengine.api.datastore import Key
from google.appengine.api import taskqueue

namespace = {}


def unicode_str(obj, encoding='utf-8'):
    """Takes an object and returns a unicode human-readable representation."""
    if isinstance(obj, str):
        return obj.decode(encoding, 'ignore')
    elif isinstance(obj, unicode):
        return obj
    return unicode(obj)


class ComputeCell(db.Model):
    exec_string = db.TextProperty()
    output = db.TextProperty()
    status = db.StringProperty()


class ExecuteWorker(webapp2.RequestHandler):
    # TODO: add some sort of bulking mechanism
    def post(self):
        key = self.request.get('key')
        cell = db.get(key)
        out = self.execute_code(cell.exec_string)
        cell.status = 'done'
        cell.output = out
        cell.put()

    def execute_code(self, code):
        """Evalue the given code, returning what is sent to stdout."""
        ans = ''
        logging.debug('running', code)
        s0 = sys.stdout
        se = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
        try:
            exec code in namespace
        except:
            ans += traceback.format_exc()
        finally:
            sys.stdout.seek(0)
            sys.stderr.seek(0)
        ans += str(sys.stdout.read()) + str(sys.stderr.read())
        sys.stdout = s0
        sys.stderr = se
        logging.debug('output', ans)
        return ans


class AJAXHandler(webapp2.RequestHandler):
    def get(self):
        key = Key(self.request.get('id'))
        cell = db.get(key)
        self.response.out.write(json.dumps({'status': cell.status,
                                            'output': cell.output
                                            }))

    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        new_cell = ComputeCell(exec_string=self.request.get('input'),
                               status='not ready', output='')
        new_cell.put()
        key = new_cell.key()
        taskqueue.add(url='/worker', params={'key': key})
        self.response.out.write(key)


class GetID(webapp2.RequestHandler):
    def get(self):
        key = Key(self.request.get('id'))
        cell = db.get(key)
        self.response.out.write(json.dumps({'exec_string': cell.exec_string}))


def main():
    application = webapp2.WSGIApplication([
        webapp2.Route('/', webapp2.RedirectHandler,
                      defaults={'_uri': 'static/index.html'}),
        ('/exec', AJAXHandler),
        ('/get_id', GetID),
        ('/worker', ExecuteWorker)], debug=True)
    application.run()


if __name__ == '__main__':
    main()
