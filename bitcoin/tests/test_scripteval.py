# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import unittest

from binascii import unhexlify

from bitcoin.script import *
from bitcoin.scripteval import *

def parse_script(s):
    def ishex(s):
        return set(s).issubset(set('0123456789abcdefABCDEF'))

    r = []

    # Create an opcodes_by_name table with both OP_ prefixed names and
    # shortened ones with the OP_ dropped.
    opcodes_by_name = {}
    for name, code in OPCODES_BY_NAME.items():
        opcodes_by_name[name] = code
        opcodes_by_name[name[3:]] = code

    for word in s.split():
        if word.isdigit() or (word[0] == '-' and word[1:].isdigit()):
            r.append(CScript([long(word)]))
        elif word.startswith('0x') and ishex(word[2:]):
            # Raw ex data, inserted NOT pushed onto stack:
            r.append(unhexlify(word[2:].encode('utf8')))
        elif len(word) >= 2 and word[0] == "'" and word[-1] == "'":
            r.append(CScript([bytes(word[1:-1].encode('utf8'))]))
        elif word in opcodes_by_name:
            r.append(CScript([opcodes_by_name[word]]))
        else:
            raise ValueError("Error parsing script: %r" % s)

    return CScript(b''.join(r))


def load_test_vectors(name):
    with open(os.path.dirname(__file__) + '/data/' + name, 'r') as fd:
        for test_case in json.load(fd):
            if len(test_case) < 3:
                test_case.append('')
            scriptSig, scriptPubKey, comment = test_case

            scriptSig = parse_script(scriptSig)
            scriptPubKey = parse_script(scriptPubKey)

            yield (scriptSig, scriptPubKey, comment, test_case)


class Test_EvalScript(unittest.TestCase):
    flags = (SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_STRICTENC)
    def test_script_valid(self):
        for scriptSig, scriptPubKey, comment, test_case in load_test_vectors('script_valid.json'):
            if not VerifyScript(scriptSig, scriptPubKey, None, 0, SIGHASH_NONE, flags=self.flags):
                self.fail('Script FAILED: %r %r %r' % (scriptSig, scriptPubKey, comment))

    def test_script_invalid(self):
        for scriptSig, scriptPubKey, comment, test_case in load_test_vectors('script_invalid.json'):
            if VerifyScript(scriptSig, scriptPubKey, None, 0, SIGHASH_NONE, flags=self.flags):
                self.fail('Script FAILED: (by succeeding) %r %r %r' % (scriptSig, scriptPubKey, comment))
