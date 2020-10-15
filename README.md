# cpp_type_builder
This is a simple python3 script that reads a json file with definitions for enum classes and structures datatypes that one would want in a program.
This codebase will generate the prototypes and definitions as well as to_string() functions for enum classes and ostream output helper to allow easier printing to console of these types.

# example execution
./cpp_type_builder json_examples/config.json

will read the example json configuration file and output a header "output/radio_types.hpp"

Peter Fetterer (KB3GTN@gmail.com)

