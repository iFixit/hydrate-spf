import re

import spf

spfPrefix = 'v=spf1'

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

    An include must do a recursive hydration of the included domain's SPF
    rules.  It will prefer the SPF record...
    >>> hydrate_mechanism('include', 'mailtank.com')
    'ip4:65.50.229.106 ip4:66.181.10.77 ip4:66.181.10.77 ip4:66.181.10.77'

    ...but fall back to SPF TXT records.
    >>> hydrate_mechanism('include', 'helpscoutemail.com')
    'ip4:23.23.237.213 ip4:74.63.63.121 ip4:74.63.63.115 ip4:54.243.205.80'
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
    if mechanism == 'include':
        records = []
        for (_, (record)) in spf.DNSLookup(value, 'spf'):
            # We get back a list of records, even if there's only one (the
            # usual case).  But the RFC says multiple records are valid, so we
            # might as well join in case there's more than one.
            # http://www.openspf.org/RFC_4408#multiple-strings
            record = ''.join(record)
            records.append(
                hydrate_record(record, domain=value, fullRecord=False))
        # Did we fail to get something from the SPF lookup?  Try TXT instead.
        if not records:
            for (_, (record)) in spf.DNSLookup(value, 'txt'):
                record = ''.join(record)
                # TXT records are used for a lot of other things.
                if record.split()[0] != spfPrefix:
                    continue

                records.append(
                    hydrate_record(record, domain=value, fullRecord=False))
        # Sort the records so the order is predictable for our tests.
        records.sort()
        return ' '.join(records)
    raise Exception('Unknown mechanism "%s"' % mechanism)

def hydrate_record(record, domain=None, fullRecord=True):
    """
    Hydrate an entire SPF record.

    :var string record: The entire SPF string, as stored in DNS.
    :var string domain: The domain of the record we're parsing.  Needed for
                        evaluating A and MX mechanisms.
    :var boolean fullRecord: Should we return the SPF version prefix and 'all'
                             modifier suffix?  `False` is useful for `include`.
    """
    spfSuffix = ''

    mechanisms = record.split()
    mechanisms.remove(spfPrefix)
    hydratedRecords = []
    for mechanism in mechanisms:
        # 'all' (and variants) ends rightward parsing.
        # http://www.openspf.org/RFC_4408#mech-all
        # Available qualifiers: http://www.openspf.org/RFC_4408#evaluation-mech
        # TODO: This regex wants to be unit-tested.
        if re.match(r'^[-+~?]?all$', mechanism):
            spfSuffix = mechanism
            break
        hydratedRecords.append(hydrate_mechanism(mechanism, domain))

    if fullRecord:
        hydratedRecords = [spfPrefix] + hydratedRecords + [spfSuffix]

    hydratedRecord = ' '.join(hydratedRecords)

    if fullRecord:
        # DNS doesn't allow individual strings to be greater than 255
        # characters.  Thankfully, the RFC specifies that multiple strings must
        # be joined without additional whitespace, so we don't need to ensure
        # we break on words.
        # http://www.openspf.org/RFC_4408#multiple-strings
        splitRecord = split_by_length(hydratedRecord, 255)
        hydratedRecord = '"%s"' % '" "'.join(splitRecord)

    return hydratedRecord

def split_by_length(string, length):
    # http://forums.devshed.com/python-programming/390312-efficient-splitting-string-fixed-size-chunks-post1627881.html#post1627881
    return [string[i:i+length] for i in range(0, len(string), length)]

