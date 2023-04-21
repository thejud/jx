jx - simple JSON field extractor

jx extracts one or more fields from json data for easy processing, similar the linux `cut` command.

    $ cat users.jsonl
    {"first": "John", "last": "Doe", "uid": 1001, "score": 85, "game": "Chess"}
    {"first": "Jane", "last": "Doe", "uid": 1002, "score": 92, "game": "Chess"}
    {"first": "Bob", "last": "Smith", "uid": 1003, "score": 77, "game": "Checkers"}


    # extract the score, uid and first name from each object
    $ jx score uid first < users.jsonl
    score  uid   first
    85     1001  John
    92     1002  Jane
    77     1003  Bob

[jq](https://stedolan.github.io/jq/) is a much better alternative for advanced
json processing, but for my very common use case of slicing out some fields, `jx`
is more concise.

    jx firstname lastname < names.json

vs.

    jq '.[] | .firstname + " " + .lastname' names.json
    or 
    jq '.[] | "\(.firstname) \(.lastname)"' names.json

Data is read from STDIN, but a file can be specified with the `-i` option.

Text table format is the default output format, but can be changed to 
TSV with the -t option, or to another delimiter with the -d option.

`jx` handles one json object per line by default. However, it will also
auto-detect an array of json objects when the input starts with `[`, e.g.

```json
[{"user":"batman", "id":1},
  {"user":"robin", "id":2}
]
```

and (less usefully) multi-line/pretty-printed json where the open '{' is on a line by itself, e.g. 

```json
{
  "user": "batman",
  "id": 1
}
```

use -s/--smart to disable this feature.

jx also provide (basic) flattening for extracting nested fields.
nested json can be flattened with `--flatten` or `-f`, and if so, nested keys
can be references with the syntax parentKey + . + childKey + index

e.g. `jx -f name.first` or `jx -f addresses.0.zipcode`

Use --join to join keys with a different delimiter, like "-", or `-F` to for "_" as the delimiter.


### Rationale

I use `jx` as part of small data processing pipelines when I need to treat API output as input to some sort of
quick aggregation, transformation and/or analysis on the command line.

For example, I might want to find the top three highest scoring users:

    $ jx score last first < test/users.jsonl | sort -nr | head -3
    96     Johansson   Scarlett
    94     Jones       Alice
    92     Doe         Jane

or, using [gnu datamash](https://www.gnu.org/software/datamash/),
I could extract the game and the user's first name, and then group them to get a list of games 
along with each player who plays that game.

    $ jx -H game first < test/users.jsonl | datamash --sort --whitespace --group 1 collapse 2
    Checkers	Bob,Alice,Chris,Scarlett
    Chess	John,Jane,Tom,Kate,Robert,Emma

If this sort of text processing is useful to you, also check out my
[text processing cookbook](https://github.com/thejud/text-processing-cookbook), 
where I describe many other techniques for quickly manipulating plain text into data for analysis.

As I mentioned previously, I use `jx` alongside `jq`. `jq` is obviously much more fully featured. However, I prefer
to extract the data I need using `jx`, and then use other standard tools for manipulating that data, rather than doing
complicated transformations with `jq` expressions. I will often use `jq` as a pre-filter for `jx`, for example to
to unpack the `results` key of a paginated results set, and then extract field names.

## EXAMPLES

    # extract the 'c' and 'a' fields from each object
    $ printf '{"a": 1, "b": 2, "c":3}\n{"a":7,"b":2,"c":20}' | jx c a
    c   a
    3   1
    20  7

    # No fields prints all values. use this to print your json data in columns.
    # pipe into `less -S` if the output gets too wide.
    $ printf '{"a": "foo", "b": 1}\n{"a":"loooooong", "b":2}' | jx 
    foo        1
    loooooong  2

    # Skip the output header row
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

    # alternate json level joiner. Default is '.'
    $  echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jx -F -j- a-c a-b
    a-c  a-b
    3    2  

    # flatten with array indexing
    $ echo '{"a": {"b": 2, "c":3, "d": [7,10]}}' | jx -F a_c a_d_0
    a_c	 a_d_0
    3    7

    # tab-separated output
    $ echo '{"a":1, "b": 2, "c":3}' | jx  -t a c
    a	c
    1	3

    # alternate output delimiter
    $ echo '{"a":1, "b": 2, "c":3}' | jx  -s '|'  a c
    a|c
    1|3

    # replace whitespace in output fields, useful for columnar output
    $ echo '{"first": "Jud D"}' | jx -w 
    first
    Jud_D

    # smart parsing: autodetect arrays of objects
    echo '[{"a":1},{"a":2}]' | jx a
    a
    1
    2

    # smart detecting multiline arrays (json pretty printed)
    echo '[{"a":1},{"a":2}]' | jq | jx a
    a
    1
    2

    # List field names found in the first object. Useful for figuring out what fields are available.
    echo '{"a": 1, "b": 2, "c":3}' | jx --names
    a
    b
    c
    
    # extract all keys from all objects
    # useful for exploring json data that may have different fields across objects
    printf '{"b":1,"a":2}\n{"b":2,"c":3}' | jx --all-keys
    b
    a
    c

    # combine with jq to extract from arbitrarily deep structures
    curl https://dummyjson.com/products | jq '.products[]' | jx id price title
    cat permissions | jq .permissions.users[] | jx id user



## INSTALLATION

pip install jextract

You can also simply copy the jextract.py binary from the src directory, as it has no dependencies.

## LIMITATIONS

1. The column pretty printer reads everything into memory so that it can compute
   proper column lengths by reading every row. If this is a problem, use the `--delimited` option
   instead and provide a delimiter, or the `-t` output for TSV output. 

2. JSON parsing makes a few assumptions:
  - If the first line non-blank link is `{`, multi-line (pretty printed) input is assumed, and the
       rest of the file is read into memory. 

  - if the input starts with `[`, array input is assumed, and the rest of the data is read into memory. 
   If you don't want this behavior, pre-process with `jq` to convert arrays in a single json object per line, like:

      jq -c '.[]' test/users_array.json | jx first last

3. Field exploration with -n or -N doesn't work very cleanly with flattening.
  - while you can combine -N and -f/-F, if your nested structure contains arrays you may have an explosion of field names.
  - 

    
## TODO

Add positional field extraction. Will require validation of fields on every
line to match the first line to prevent silently dropping/munging columns


## AUTHOR

Jud Dagnall <github@dagnall.net>
