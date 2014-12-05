##############################################################################
#
# Copyright (c) Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from zope.testing import renormalizing, setupstack
import doctest
import unittest
import manuel.capture
import manuel.doctest
import manuel.testing
import mock
import pprint
import re
import time


class Logging:

    trace = True

    def log(self, *args):
        if self.trace:
            print self.__class__.__name__, ' '.join(args)

class MemoryDB:

    def __init__(self, config):
        self.agents = {}
        self.alerts = {}
        self.faults = {}
        self.squelches = []

    def heartbeat(self, agent, status):
        self.agents[agent] = dict(
            agent=agent,
            updated=time.time(),
            status=status)

    def old_agents(self, min_age):
        now = time.time()
        for data in agents.values():
            agent_age = now - data['updated']
            if agent_age > min_age:
                yield data.copy()

    def alert_start(self, name):
        self.alerts[name] = time.time()

    def alert_finished(self, name):
        self.alerts.pop(name, None)

    def old_alerts(self, min_age):
        now = time.time()
        for name, start in alerts.items():
            age = now - start
            if age > min_age:
                yield name

    def get_faults(self, agent):
        return self.faults[agent]

    def set_faults(self, agent, faults):
        self.faults[agent] = faults

    def get_squelches(self):
        return list(self.squelches)

    def __str__(self):
        return pprint.pformat(dict(
            agents=self.agents, alerts=self.alerts, faults=self.faults))

class OutputAlerter(Logging):

    def __init__(self, config):
        pass

    def trigger(self, name, message):
        self.log('trigger', name, message)

    def resolve(self, name):
        self.log('resolve', name)

filecheck_py = """
import os, sys, time

[name] = sys.argv[1:]
if os.path.isfile(name):
  status = 0
  with open(name) as f:
     data = f.read()
  if len(data) == 0:
     print '%r exists, but is empty' % name
     sys.exit(1)
  if data == 'noout':
     sys.exit(0)
  if data[0] == '{':
     print data
     sys.exit(0)

  status = 0
  if data == 'stderr':
     sys.stderr.write('what hapenned?')
  elif data == 'status':
     status = 42
  elif data == 'sleep':
     time.sleep(2)
  print '%r exists' % name
  sys.exit(status)
print "%r doesn't exist" % name
sys.exit(2)
""" # ' sigh

def setUp(test):
    setupstack.setUpDirectory(test)
    with open('filecheck.py', 'w') as f:
        f.write(filecheck_py)

    setupstack.context_manager(
        test, mock.patch('socket.getfqdn', return_value='test.example.com'))

def test_suite():
    return unittest.TestSuite((
        manuel.testing.TestSuite(
            manuel.doctest.Manuel(
                optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                checker=renormalizing.OutputChecker([
                    (re.compile(r"'updated': \d+(\.\d*)?"), '')
                    ])
                ) + manuel.capture.Manuel(),
            'agent.rst',
            setUp = setUp, tearDown=setupstack.tearDown),
        ))
