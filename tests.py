"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

import update

class SimpleTest(TestCase):
	def test_basic_addition(self):
		"""
		Tests that 1 + 1 always equals 2.
		"""
		self.assertEqual(1 + 1, 2)

	def test_update_fetch_data_bad_addr(self):
		remote = "ssh -o 'BatchMode yes' badaddress"

		co1, co2, errno1, errno2 = update.fetch_data(remote)

		self.assertEqual(errno1, 255)
		self.assertEqual(errno2, 255)
		self.assertEqual(co1, '')
		self.assertEqual(co2, '')

	def test_update_fetch_data_bad_cmd(self):
		remote = "sssh -o 'BatchMode yes' localhost"

		co1, co2, errno1, errno2 = update.fetch_data(remote)

		self.assertEqual(errno1, 127)
		self.assertEqual(errno2, 127)
		self.assertEqual(co1, '')
		self.assertEqual(co2, '')

	def test_update_fetch_data_fail_batch_mode(self):
		remote = "ssh -o 'BatchMode yes' localhost"

		co1, co2, errno1, errno2 = update.fetch_data(remote)

		self.assertEqual(errno1, 255)
		self.assertEqual(errno2, 255)
		self.assertEqual(co1, None)
		self.assertEqual(co2, None)

	def test_update_fetch_data_fail_batch_mode(self):
		remote = "ssh -o 'BatchMode yes' brett"

		co1, co2, errno1, errno2 = update.fetch_data(remote)

		self.assertEqual(errno1, 0)
		self.assertEqual(errno2, 0)
		self.assertNotEqual(co1, None)
		self.assertNotEqual(co2, None)
		self.assertEqual(errno1 == 0 and co1 is not None, True)
		self.assertEqual(errno2 == 0 and co2 is not None, True)
