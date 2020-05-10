import unittest
import getNumberOfReplies
import json
from unittest.mock import MagicMock
from messagebox import MessageBox

class Tests(unittest.TestCase):
    def setUp(self):
        text = open("fixtures.json", 'r')
        self.parsed_json = json.loads(text.read())
        self.messageBoxMock = MessageBox()
        self.messageBoxMock.displayMessageBox = MagicMock()
        text.close()

    def testExcludedPhrases(self):
        getNumberOfReplies.signupChecker(True, self.parsed_json["testExcludedPhrases1"], [], 1, None, self.messageBoxMock)
        self.messageBoxMock.displayMessageBox.assert_not_called()

    def testExcludedPhrasesWhenParentIsAReply(self):
        getNumberOfReplies.signupChecker(True, self.parsed_json["testExcludedPhrases2"], [], 1, None, self.messageBoxMock)
        self.messageBoxMock.displayMessageBox.assert_not_called()

    def testSignupCheckerDefault(self):
        getNumberOfReplies.signupChecker(True, self.parsed_json["testSignUpCheckerDefault"], [], 1, None, self.messageBoxMock)
        self.messageBoxMock.displayMessageBox.assert_called()

    def testExcludesDeliveries(self):
        getNumberOfReplies.signupChecker(True, self.parsed_json["testExcludesDeliveries"], [], 1, None, self.messageBoxMock)
        self.messageBoxMock.displayMessageBox.assert_not_called()

if __name__ == '__main__':
    unittest.main()