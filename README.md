# hydrate-spf

A tool to convert an SPF record with nested lookups into a flat list of IPs.

## Motivation

[SPF] is a framework for helping combat spam.  [It is very
easy][too-many-records] to include more dynamic lookups than [the RFC allows],
particularly when the records you include do their own includes.  Since an SPF
record that fails validation due to too many lookups may lead to emails getting
erroneously marked as spam, we need to condense the number of lookups while
still retaining the same information.

This means we're effectively caching the information of others' SPF records,
which defeats the point of having includes (namely, that they can update their
records without notifying all their customers).  However, if we can update the
caches automatically, we can keep them updated enough to not be a problem.

The term "hydration" is borrowed from [certain ORMs], where it refers to
filling an object with data looked up from the database.

[SPF]: https://en.wikipedia.org/wiki/Sender_Policy_Framework
[too-many-records]: http://stackoverflow.com/q/14261214/120999
[the RFC allows]: http://www.openspf.org/RFC_4408#mech-mx
[certain ORMs]: http://propelorm.org/documentation/03-basic-crud.html#retrieving-rows

## Installation

    [$]> pip install hydrate_spf

or

    [$]> easy_install hydrate_spf

### Hacking

If you want to install it locally to hack on it, install hydrate-spf from git:

    [$]> git clone git@github.com:iFixit/hydrate-spf.git
    [$]> virtualenv --no-site-packages --distribute env
    [$]> source env/bin/activate
    [$]> pip install -r requirements.txt
    [$]> pip install -e .

## Usage

    [$]> ./hydrate-spf.py --help
    hydrate-spf
    
    Usage:
        hydrate-spf <record> <domain>
        hydrate-spf [-v] test
        hydrate-spf --version
        hydrate-spf (-h | --help)
    
    Options:
        -v            Verbose test output.
           --version  Show version.
        -h --help     Show this screen.
    [$]> ./hydrate-spf.py 'v=spf1 a mx ~all' ifixit.com
    "v=spf1 ip4:75.101.159.182 ip4:173.203.2.36 ip4:98.129.184.4 ~all"

### Caveats

A hydrated record containing an `include` mechanism will not behave in exactly
the same way it would prior to hydration.  `include`s are more accurately
recursive calls, which means the modifier on the included record's `all` is
used when evaluating its rules; a hydrated record will only use the modifier
specified at the top-level record.

Also, `SPF` records are preferred over `TXT` records when processing an
`include`.  RFC 4408 states that if there are both `TXT` and `SPF` records,
they *must* be the same; we don't know what common implementations do when
presented with differing records, so we can't guarantee conformance.

## Changes

### v0.2.0

* Hydrated records are now returned inside double quotes.
* Hydrated records longer than 255 characters are split into multiple strings.

## License

hydrate-spf is offered under the permissive [zlib license].  See `LICENSE` for
details.

[zlib license]: http://opensource.org/licenses/Zlib

