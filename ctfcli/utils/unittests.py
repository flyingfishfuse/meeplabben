

"""Unittest with DocTests."""


import doctest
import unittest
import yaml
import __main__
from random import randint
import os,sys
sys.path.insert(0, os.path.abspath('.'))
import ctfcli.utils.utils
import ctfcli.core.ctfdrepo
import ctfcli.core.apisession
import ctfcli.ClassConstructor
import ctfcli
import ctfcli.linkage
import __main__
import os,sys
from pathlib import Path
from ctfcli.core.masterlist import Masterlist
from ctfcli.core.repository import Repository
from ctfcli.core.ctfdrepo import SandboxyCTFdRepository
from ctfcli.core.apisession import APIHandler
from ctfcli.core.gitrepo import SandboxyGitRepository
from ctfcli.utils.utils import redprint,greenprint, errorlogger
from ctfcli.utils.config import Config

# Random order for tests runs. (Original is: -1 if x<y, 0 if x==y, 1 if x>y).
unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: randint(-1, 1)


def setUpModule():
    """
    """

def tearDownModule():
    pass


def load_tests(loader, tests, ignore):  # Returns empty TestSuite if fails.
    """Convert DocTests from module to unittest.TestSuite."""
    tests.addTests(doctest.DocTestSuite(module=None, setUp=None, tearDown=None))
    return tests  # Returned tests run with the rest of unittests.

class TestCode(unittest.TestCase):
    """
    Unit testing for things
    """
    
    maxDiff, __slots__ = None, ()

    def __init__(self):
        """
        searches pwd for the assets given in list fed to class on init
        """
        # define the items to test
        # I want to make sure the yaml loader code works on the 
        # yaml files its expected to work with, in combination with the linter
        self.testsubjects = ["deployment.yml","challenge.yml", "service.yml"]
        # get the paths
        self.testsubjectpaths = [getpath(pathything) for pathything in self.testsubjects]
        
        
    def loadyamlfiles(self,pathoffile:Path):
        """
        feeds Yaml().loadyaml()
        """
        dictofyaml = Yaml().loadyaml(pathoffile)
        # check if its even a dict, who knows right?
        self.assertEqual(dict,dictofyaml)

    def test_toplevel(self):
        """
        
        """
        self._ctfdops = SandboxyCTFdRepository(self.repofolder, self.masterlistlocation)

    def test_masterlist(self):
        """
        
        """
        masterlist = Masterlist()
        newrepo = Repository(**dictofcategories)
        masterlist._writenewmasterlist(self.masterlistlocation, newrepo,filemode="w")
    # functions to run as tests 
    # MUST be prepended with the string 
    # TEST
    def test_yamlloader(self,yamlfile:Path):
        """
        tests loading of deployment/service/challenge files
        
        """
        for path in self.testsubjectpaths:
            self.loadyamlfiles(path)
            pass

    def tearDown(self):
        """Method to tear down the test fixture. Run AFTER the test methods."""
        pass

    def addCleanup(self, function, *args, **kwargs):
        """Function called AFTER tearDown() to clean resources used on test."""
        pass

    @classmethod
    def setUpClass(cls):
        """Class method called BEFORE tests in an individual class run. """
        pass  # Probably you may not use this one. See setUp().

    @classmethod
    def tearDownClass(cls):
        """Class method called AFTER tests in an individual class run. """
        pass  # Probably you may not use this one. See tearDown().

    @unittest.skip("Demonstrating skipping")  # Skips this test only
    @unittest.skipIf("boolean_condition", "Reason to Skip Test here.")  # Skips this test only
    @unittest.skipUnless("boolean_condition", "Reason to Skip Test here.")  # Skips this test only
    @unittest.expectedFailure  # This test MUST fail. If test fails, then is Ok.
    def test_dummy(self):
        self.skipTest("Just examples, use as template!.")  # Skips this test only
        self.assertEqual(a, b)  # a == b
        self.assertNotEqual(a, b)  # a != b
        self.assertTrue(x)  # bool(x) is True
        self.assertFalse(x)  # bool(x) is False
        self.assertIs(a, b)  # a is b
        self.assertIsNot(a, b)  # a is not b
        self.assertIsNone(x)  # x is None
        self.assertIsNotNone(x)  # x is not None
        self.assertIn(a, b)  # a in b
        self.assertNotIn(a, b)  # a not in b
        self.assertIsInstance(a, b)  # isinstance(a, b)
        self.assertNotIsInstance(a, b)  # not isinstance(a, b)
        self.assertAlmostEqual(a, b)  # round(a-b, 7) == 0
        self.assertNotAlmostEqual(a, b)  # round(a-b, 7) != 0
        self.assertGreater(a, b)  # a > b
        self.assertGreaterEqual(a, b)  # a >= b
        self.assertLess(a, b)  # a < b
        self.assertLessEqual(a, b)  # a <= b
        self.assertRegex(s, r)  # r.search(s)
        self.assertNotRegex(s, r)  # not r.search(s)
        self.assertItemsEqual(a, b)  # sorted(a) == sorted(b) and works with unhashable objs
        self.assertDictContainsSubset(a, b)  # all the key/value pairs in a exist in b
        self.assertCountEqual(a, b)  # a and b have the same elements in the same number, regardless of their order
        # Compare different types of objects
        self.assertMultiLineEqual(a, b)  # Compare strings
        self.assertSequenceEqual(a, b)  # Compare sequences
        self.assertListEqual(a, b)  # Compare lists
        self.assertTupleEqual(a, b)  # Compare tuples
        self.assertSetEqual(a, b)  # Compare sets
        self.assertDictEqual(a, b)  # Compare dicts
        # To Test code that MUST Raise Exceptions:
        self.assertRaises(SomeException, callable, *args, **kwds)  # callable Must raise SomeException
        with self.assertRaises(SomeException) as cm:
            do_something_that_raises() # This line  Must raise SomeException
        # To Test code that MUST Raise Warnings (see std lib warning module):
        self.assertWarns(SomeWarning, callable, *args, **kwds)  # callable Must raise SomeWarning
        with self.assertWarns(SomeWarning) as cm:
            do_something_that_warns() # This line  Must raise SomeWarning
        # Assert messages on a Logger log object.
        self.assertLogs(logger, level)
        with self.assertLogs('foo', level='INFO') as cm:
            logging.getLogger('foo').info('example message')  # cm.output is 'example message'


if __name__.__contains__("__main__"):
    print(__doc__)
    unittest.main()
    # Run just 1 test.
