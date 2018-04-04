# -*- coding: utf-8 -*-
import unittest

from openprocurement.contracting.esco.tests import (
    contract,
    change,
    document,
    milestone,
)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(contract.suite())
    suite.addTest(change.suite())
    suite.addTest(document.suite())
    suite.addTest(milestone.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
