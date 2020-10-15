#!/usr/bin/python3
# Peter Fetterer (KB3GTN@gmail.com)
# 10/15/2020
#
# simple program to generate typedata headers based on json input
# json imput defines structs and enum classes and will generate some helper functions
# to support simpler development.

import os
import json
import sys
from io import StringIO
import shutil
import datetime


class cpp_type_builder:
    def __init__(self):
        self.config_dict = {}
        self.structs = {}
        self.enumtypes = {}
        self.config_file = ""
        self.prototypes = StringIO()  # prototypes for the top of the file
        self.header_output = StringIO()  # output content for definitions

    def read_config(self,config_file):
        """ 
            config_file -- python string of config json file to read
        """
        self.config_file = config_file
        try:
            with open(config_file) as f:
                self.config_dict = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print("Parser Error line "+str(e.lineno)+" col "+str(e.colno)+" : "+e.msg)
            raise e
        except FileNotFoundError as e:
            print("failed to open config file "+config_file)
            raise e

    def _get_inputs(self):
        """ look for types that are format "struct" """
        for entry in self.config_dict["type_list"]:
            type_name = list(entry.keys())[0]
            type_format = entry[type_name]["format"]
            if type_format == "struct":
                self.structs[type_name] = entry[type_name]
            elif type_format == "enum_class":
                self.enumtypes[type_name] = entry[type_name]

        # debug prints
        #print("input struct types: ")
        #print(json.dumps(self.structs))
        #print("input enum_class types: ")
        #print(json.dumps(self.enumtypes))

    def build_header(self):
        """ build header output file.. """
        self._get_inputs()
        self._build_enums()
        self._build_structs()
        with open(self.config_dict['output_header_file'], 'w') as fd:
            #_build_structs()

            # write file boiler plate stuff
            hdr_name = self.config_dict["output_header_file"]
            hdr_name = os.path.basename(hdr_name)
            hdr_name = hdr_name.replace('.', '_')
            hdr_name = hdr_name.replace('/', '_')
            hdr_name = hdr_name.replace('\\', '_')
            # include guards for file.
            print("// auto generated file, edits may be overwritten.", file=fd)
            print("// generated from source json file "+self.config_file+' at {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), file=fd )
            print("#ifndef __"+hdr_name+"__", file=fd)
            print("#define __"+hdr_name+"__", file=fd)
            print("", file=fd)
            print("// standard include files..", file=fd);
            print("#include <string>", file=fd)
            print("#include <cstring>", file=fd)
            print("#include <cstdint>", file=fd)
            print("#include <iostream>", file=fd)

            print("", file=fd)
            # print out all the prototypes
            print("////////////////////////////////////////////////////////", file=fd)
            print("// Prototypes for defined datatypes and helper functions", file=fd)
            print("////////////////////////////////////////////////////////", file=fd)
            # write in the prototype buffer
            print(self.prototypes.getvalue(), file=fd)
            # print out all the definitions
            print("////////////////////////////////////////////////////////", file=fd)
            print("// definitions for all data types hand helper functions", file=fd)
            print("////////////////////////////////////////////////////////", file=fd)
            print(self.header_output.getvalue(), file=fd)
            print("", file=fd)
            
            #end include guard
            print("#endif  // end include guard", file=fd)

    def _build_enums(self):
        """ build c++ enum class data structure, add
            to_string implementation and ostream << overload for cout usage
        """
        for dt in self.enumtypes:
            entry = self.enumtypes[dt]
            print("building enum class for type "+dt)
            print("enum class "+str(dt)+" : "+str(entry["basetype"])+";", file=self.prototypes)

            print("", file=self.header_output)
            print("////////////////////////////////////////////////////////", file=self.header_output)
            print("enum class "+str(dt)+" : "+str(entry["basetype"])+" {", file=self.header_output)
            # build class definition
            start_of_list=1
            for e in entry["enum_entries"]:
                # first time though don't print starting ','
                if start_of_list ==1: 
                    start_of_list=0
                else:
                    print(",", file=self.header_output)
                print("    "+e, file=self.header_output, end='')
            print('', file=self.header_output) # get newline on end of last item.
            print("};", file=self.header_output)
            print('', file=self.header_output)
            # build to_string translator
            print("std::string to_string("+str(dt)+" v);", file=self.prototypes)
            print("std::string to_string("+str(dt)+" v) {", file=self.header_output)
            print("    switch(v) {", file=self.header_output)
            for e in entry["enum_entries"]:
                print("       case "+str(dt)+"::"+e.split("=")[0]+":", file=self.header_output)
                print("           return std::string(\""+e.split("=")[0]+"\");", file=self.header_output)
            print("       default:", file=self.header_output)
            print("           return std::string(\"unknown value: \"+std::to_string(static_cast<"+str(entry["basetype"])+">(v)));", file=self.header_output)
            print("    }", file=self.header_output)
            print("}", file=self.header_output)
            print('', file=self.header_output)
            # build ostream helper
            print("std::ostream& operator <<(std::ostream& os, const "+str(dt)+"& m);", file=self.prototypes)
            print("std::ostream& operator <<(std::ostream& os, const "+str(dt)+"& m) {", file=self.header_output)
            print("    os << to_string(m);", file=self.header_output )
            print("    return os;", file=self.header_output)
            print("}", file=self.header_output)
            print('', file=self.header_output)

            #debug print
            #print("prototypes: ")
            #print(self.prototypes.getvalue())
            #print("definitions: ")
            #print(self.header_output.getvalue())


    def _build_structs(self):
        """
        Build structures codec in header
        """
        for st in self.structs:
            print("building struct for type "+st)
            entry = self.structs[st]
            # generate prototype
            print("struct "+st+";", file=self.prototypes)
            # generate definition
            print("////////////////////////////////////////////////////////", file=self.header_output)
            print("struct "+st+" {", file=self.header_output)
            for member in entry["entries"]:
                print("    "+member["datatype"]+" "+member["name"]+";", file=self.header_output)
            print("};", file=self.header_output)
            print("", file=self.header_output)
            # generate ostream helper for this struct, assumes all members have ostream overloads
            print("std::ostream& operator <<(std::ostream& os, const "+str(st)+"& m);", file=self.prototypes)
            print("std::ostream& operator <<(std::ostream& os, const "+str(st)+"& m) {", file=self.header_output)
            print("    os << \"struct "+st+" {\";", file=self.header_output)
            for member in entry["entries"]:
                print("    os << ' ' << \""+member["name"]+":\" << m."+member["name"]+";", file=self.header_output)
            print("    os << \" }\";", file=self.header_output)
            print("    return os;", file=self.header_output)
            print("}", file=self.header_output)

     
def main(config_file):
    tb = cpp_type_builder()
    tb.read_config(config_file)
    tb.build_header()



# launch main entry point if call as top level python script.
if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main("config.json")


