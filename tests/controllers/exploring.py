#!/usr/bin/python
#found when running python web2py.py -S paideia -M -R testRunner.py

import unittest
from gluon.globals import Request, Session, Storage, Response
from gluon.contrib.test_helpers import form_postvars

class ExploringController(unittest.TestCase):
	def setUp(self):
		pass

	def testIndex(self):
		#form_postvars()
		self.assertEquals(2,3)
		self.assertEquals(2,2)