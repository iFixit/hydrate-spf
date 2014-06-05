#!/usr/bin/env python

import spf

def hydrate_mechanism(mechanism, domain=None):
    """
    A mechanism is an entry in an SPF record that dictates a server or set of
    servers to approve for mail-sending.

        http://www.openspf.org/RFC_4408#mechanisms

    There are many types of records, but they all eventually resolve to IP
    addresses (or blocks of addresses).  These resolved addresses are what
    we're trying to return.

    When taking in a single address, we should just return it:
    >>> hydrate_mechanism('ip4:66.181.10.77')
    'ip4:66.181.10.77'

    The same thing goes for address blocks:
    >>> hydrate_mechanism('ip4:67.192.241.0/24')
    'ip4:67.192.241.0/24'

    A records should be converted to their resolved IPs.
    >>> hydrate_mechanism('a', 'ifixit.com')
    'ip4:75.101.159.182'

    Even if there are multiple resolutions.
    >>> hydrate_mechanism('a', 'microsoft.com')
    'ip4:134.170.188.221 ip4:65.55.58.201'

    MX records should similarly be resolved.
    >>> hydrate_mechanism('mx', 'ifixit.com')
    'ip4:173.203.2.36 ip4:98.129.184.4'
    """
    (mechanism, value, netmask, netmask6) = spf.parse_mechanism(mechanism, domain)
    if mechanism == 'ip4':
        hydration = '%s:%s' % (mechanism, value)
        if netmask:
            hydration += ('/%s' % netmask)
        return hydration
    if mechanism == 'a':
        records = []
        for (_, ip) in spf.DNSLookup(value, 'a'):
            records.append('ip4:%s' % ip)
        # Sort the records so the order is predictable for our tests.
        records.sort()
        return ' '.join(records)
    if mechanism == 'mx':
        records = []
        for (_, (_, domain)) in spf.DNSLookup(value, 'mx'):
            # MX records give us back a domain, so we need to do another
            # lookup.
            records.append(hydrate_mechanism('a:%s' % domain))
        # Sort the records so the order is predictable for our tests.
        records.sort()
        return ' '.join(records)
    raise Exception('Unknown mechanism %s' % mechanism)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

