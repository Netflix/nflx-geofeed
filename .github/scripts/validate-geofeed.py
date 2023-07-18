#!/usr/bin/python
#
# Copyright (c) 2012 IETF Trust and the persons identified as
# authors of the code.  All rights reserved.  Redistribution and use
# in source and binary forms, with or without modification, is
# permitted pursuant to, and subject to the license terms contained
# in, the Simplified BSD License set forth in Section 4.c of the
# IETF Trust's Legal Provisions Relating to IETF
# Documents (http://trustee.ietf.org/license-info).

"""Simple format validator for self-published ipgeo feeds.

This tool reads CSV data in the self-published ipgeo feed format
from the standard input and performs basic validation.  It is
intended for use by feed publishers before launching a feed.
"""

import csv
import ipaddr
import re
import sys

class IPGeoFeedValidator(object):
    def __init__(self):
        self.prefixes = {}
        self.line_number = 0
        self.output_log = {}
        self.SetOutputStream(sys.stderr)

    def Validate(self, feed):
        """Check validity of an IPGeo feed.

        Args:
            feed: iterable with feed lines
        """

        for line in feed:
            self._ValidateLine(line)

    def SetOutputStream(self, logfile):
        """Controls where the output messages go do (STDERR by default).

        Use None to disable logging.

        Args:
            logfile: a file object (e.g., sys.stdout) or None.
        """
        self.output_stream = logfile

    def CountErrors(self, severity):
        """How many ERRORs or WARNINGs were generated."""
        return len(self.output_log.get(severity, []))

    ############################################################
    def _ValidateLine(self, line):
        line = line.rstrip('\r\n')
        self.line_number += 1
        self.line = line.split('#')[0]
        self.is_correct_line = True

        if self._ShouldIgnoreLine(line):
            return

        fields = [field for field in csv.reader([line])][0]

        self._ValidateFields(fields)
        self._FlushOutputStream()

    def _ShouldIgnoreLine(self, line):
        line = line.strip()
        if line.startswith('#'):
            return True
        return len(line) == 0

    ############################################################
    def _ValidateFields(self, fields):
        assert(len(fields) > 0)

        is_correct = self._IsIPAddressOrPrefixCorrect(fields[0])

        if len(fields) > 1:
            if not self._IsAlpha2CodeCorrect(fields[1]):
                is_correct = False

        if len(fields) > 2 and not self._IsRegionCodeCorrect(fields[2]):
            is_correct = False

        if len(fields) != 5:
            self._ReportWarning('5 fields were expected (got %d).'
                                % len(fields))

    ############################################################
    def _IsIPAddressOrPrefixCorrect(self, field):
        if '/' in field:
            return self._IsCIDRCorrect(field)
        return self._IsIPAddressCorrect(field)

    def _IsCIDRCorrect(self, cidr):
        try:
            ipprefix = ipaddr.IPNetwork(cidr)
            if ipprefix.network._ip != ipprefix._ip:
                self._ReportError('Incorrect IP Network.')
            return False
            if ipprefix.is_private:
                self._ReportError('IP Address must not be private.')
            return False
        except:
            self._ReportError('Incorrect IP Network.')
            return False
        return True

    def _IsIPAddressCorrect(self, ipaddress):
        try:
            ip = ipaddr.IPAddress(ipaddress)
        except:
            self._ReportError('Incorrect IP Address.')
            return False
        if ip.is_private:
            self._ReportError('IP Address must not be private.')
            return False
        return True

    ############################################################
    def _IsAlpha2CodeCorrect(self, alpha2code):
        if len(alpha2code) == 0:
            return True
        if len(alpha2code) != 2 or not alpha2code.isalpha():
            self._ReportError(
                'Alpha 2 code must be in the ISO 3166-1 alpha 2 format.')
            return False
        return True

    def _IsRegionCodeCorrect(self, region_code):
        if len(region_code) == 0:
            return True
        if '-' not in region_code:
            self._ReportError('Region code must be in ISO 3166-2 format.')
            return False

        parts = region_code.split('-')
        if not self._IsAlpha2CodeCorrect(parts[0]):
            return False
        return True

    ############################################################
    def _ReportError(self, message):
        self._ReportWithSeverity('ERROR', message)

    def _ReportWarning(self, message):
        self._ReportWithSeverity('WARNING', message)

    def _ReportWithSeverity(self, severity, message):
        self.is_correct_line = False
        output_line = '%s: %s\n' % (severity, message)

        if severity not in self.output_log:
            self.output_log[severity] = []
        self.output_log[severity].append(output_line)

        if self.output_stream is not None:
            self.output_stream.write(output_line)

    def _FlushOutputStream(self):
        if self.is_correct_line: return
        if self.output_stream is None: return

        self.output_stream.write('line %d: %s\n\n'
                                % (self.line_number, self.line))

############################################################
def main():
    feed_validator = IPGeoFeedValidator()
    feed_validator.Validate(sys.stdin)

    if feed_validator.CountErrors('ERROR'):
        sys.exit(1)

if __name__ == '__main__':
    main()
