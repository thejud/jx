# jx - simple JSON field extractor

jx is intended to be used to trivially extract fields from json data.
Text table format is the default output format, but can be changed to 
TSV with the -t option, or to another delimiter with with the -d option.

jx will also auto-detect array input, and paginated input by
looking at the first line, so you can send paginated results (with
a total and items key in the first line), or first line starts with '['

use -s/--smart to disable this smartness

jx also provide (basic) flattening for extracting nested fields.
nested json can be flattened with --flatten, and if so, nested keys
can be references with the syntax key1 + . + key2 + index

e.g. name.first or addresses.0.zipcode

Use --join to join keys with a different delimiter, like "-"

[jq](https://stedolan.github.io/jq/) is a much better alternative for advanced
json processing, but for my very common use case of slicing out some fields, jx
is more concise. I frequently use jq to pre-filter data, and then jx to extract fields.

    jq '.[] | .firstname + " " + .lastname
    or 
    jq '.[] | "\(.firstname) \(.lastname)"'

vs.

    jx firstname lastname

## EXAMPLES

    # extract the 'c' and 'a' fields from each object
    $ printf '{"a": 1, "b": 2, "c":3}\n{"a":7,"b":2,"c":20}' | jx c a
    c   a
    3   1
    20  7

    # columnar output is the default. No fields prints all values
    $ printf '{"a": "foo", "b": 1}\n{"a":"loooooong", "b":2}' | jx 
    foo        1
    loooooong  2

    # no headers
    $ echo '{"a": 1, "b": 2, "c":3}' | jx -H c a
    3  1


    # flatten with dot
    # with -f or -F, should be easy to separate keys from parents
    $ echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jx -f a.c a.b
    a.c  a.b
    3    2

    # flatten with _
    $ echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jx -F a_c a_b
    a_c  a_b
    3    2

    # flatten with array indexing
    $ echo '{"a": {"b": 2, "c":3, "d": [7,10]}}' | jx -F a_c a_d_0
    a_c	 a_d_0
    3    7

    # get field names from first line
    echo '{"a": 1, "b": 2, "c":3}' | jx --names
    a
    b
    c

    # alternate json level joiner. Default is '.'
    $  echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jx -F -j- a-c a-b
    a-c  a-b
    3    2  
    
    # tab-separated output
    $ echo '{"a":1, "b": 2, "c":3}' | jx  -t a c
    a	c
    1	3

    # alternate output delimiter
    $ echo '{"a":1, "b": 2, "c":3}' | jx  -s '|'  a c
    a|c
    1|3

    # collapse whitespace in output fields, useful for columnar output
    $ echo '{"first": "Jud D"}' | jx -w 
    first
    Jud_D

    # smart parsing: autodetect arrays
    echo '[{"a":1},{"a":2}]' | jx a
    a
    1
    2

    # smart detecting multiline arrays (json pretty printed)
    echo '[{"a":1},{"a":2}]' | jq | jx a
    a
    1
    2

    # smart parsing: autodetect paged sets (with items and total)
    $ echo '{"total":2,"items":[{"a":1},{"a":2"}]}' | jx a
    a
    1
    2

    # smart detecting multiline paged sets (json pretty printed)
    echo '{"items":[{"a":1},{"a":2}]}' | jq | jx a
    a
    2

    # turn off smart parsing
    $ echo '{"total":2,"items":[{"a":1},{"a":2}]}' | jx -s items
    items
    [{"a":1},{"a":2}]}

    # extract all keys from all objects
    # useful for exploring json data that may have different keynames across objects
    printf '{"b":1,"a":2}\n{"b":2,"c":3}' | jx --all-keys
    b
    a
    c


    # combine with jq to extract non-standard paged sets, e.g. 
    curl xxx | jq '.events[]' | jx id user


## INSTALLATION

copy jx from the bin directory


    
## TODO

Add a better install procedure.

Add positional field extraction. Will require validation of fields on every
line to match the first line to prevent silently dropping/munging columns

Make the smart page set detection configurable. Better for environments that
use different conventions to indicate paged sets. Note that you can use jq to
extract only the objects you want, then extract the desired fields with jx:

    jq '.permissions.users[]' | jx id name

## AUTHOR

Jud Dagnall <github@dagnall.net>
