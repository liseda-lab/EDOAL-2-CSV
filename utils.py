import xml.etree.ElementTree as ET
import pandas as pd
import re
import os

class Parser:
    
    def __init__(self, ref):
        # Namespaces
        if(ref == True):
            self.edoal_namespace = "{http://ns.inria.org/edoal/1.0/#}"
        else:
            self.edoal_namespace = "{http://ns.inria.org/edoal/1.0/}"
        self.rdf_namespace = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
        self.ont_web_format = "{http://knowledgeweb.semanticweb.org/heterogeneity/alignment#}"
        self.rdfs_namespace ="{http://www.w3.org/2000/01/rdf-schema#}"

         # EDOAL elements
        self.restriction1 = ['PropertyDomainRestriction', 'RelationDomainRestriction','RelationCoDomainRestriction']
        self.restriction2 = ['AttributeDomainRestriction', 'AttributeOccurenceRestriction']
        self.basic_elements = ['Property', 'Class', 'Relation']
        self.construction = ['and','or','not','compose','inverse']

    # This method extracts the mappings from an edoal alignment
    def extract_mappings(self,rdf_path):    
        tree = ET.parse(rdf_path)
        root = tree.getroot()
        mappings = []

        for _map in root[0].findall("{}map".format(self.ont_web_format)):
            cell = _map.find("{}Cell".format(self.ont_web_format))
            ent1 = cell.find("{}entity1".format(self.ont_web_format))
            ent2 = cell.find("{}entity2".format(self.ont_web_format))
            ent1, ent1_type, const1 = self.parse_entity(ent1)
            ent2, ent2_type, const2 = self.parse_entity(ent2)
            type_aln = self.get_type_aln(const1, const2, ent1_type, ent2_type) 
            measure = float(cell.find("{}measure".format(self.ont_web_format)).text)
            relation = cell.find("{}relation".format(self.ont_web_format)).text

            mappings.append(
            pd.DataFrame(
                data={
                    "ent1_type":[ent1_type],
                    "entity1": [ent1],
                    "constructor1": [const1],
                    "ent2_type": [ent2_type],
                    "entity2": [ent2],
                    "constructor2": [const2],
                    "type_of_alignment": [type_aln],
                    "measure": [measure],
                    "relation": [relation]
                }
            )
        )
        return pd.concat(mappings, ignore_index=True)

    # This method parses the edoal entity elements to a more human readable form
    def parse_entity(self, entity):
        # (global) entity type is the first element inside the <entity1> element
        ent_type = str(entity[0]).split("'")[1].replace(self.edoal_namespace, "")
        ent_value = ""

        #Simple expressions
        if(len(entity[0])<1):
            ent_value = entity[0].get('{}about'.format(self.rdf_namespace))
            c = "-"

        #Complex expressions
        for ent in entity[0]:
            # Get self.construction operator
            c = str(ent).split("'")[1].replace(self.edoal_namespace, "")
            if c in self.construction:
                # Process expressions inside constructor
                ent_value += self.recursive(ent)

            # AttributeRestrictions
            elif c == "onAttribute":
                ent_value += "onAttribute: " + self.recursive(ent)
                continue
            elif c == "class": 
                ent_value += "class: " + ent[0].get('{}about'.format(self.rdf_namespace))
                c="-"
                continue
            elif c == "exists": 
                ent_value += "class: " + self.recursive(ent)
                c="-"
                continue
            elif c == "comparator":
                comparator = ent.get('{}resource'.format(self.rdf_namespace))
                ent_value += " comparator: " + str(comparator).split("#")[1];
                c="-"
                continue
            elif c == "value":
                if ent.text != None:
                    ent_value += ", value: " + ent.text
                else:
                    if (ent[0].tag == "{}Literal".format(self.edoal_namespace)):
                        ent_value += ", value: " + ent[0].get('{}string'.format(self.edoal_namespace))
                    if (ent[0].tag == "{}Instance".format(self.edoal_namespace)):
                        ent_value += ", value: " + ent[0].get('{}about'.format(self.edoal_namespace))
                c="-"
                continue
            elif c == "{http://knowledgeweb.semanticweb.org/heterogeneity/alignment#}datatype": 
                ent_value += ", datatype: " + ent[0].get('{}about'.format(self.rdf_namespace))
                c="-"
                continue

        return ent_value, ent_type, c

    #This method self.recursively processes the nested expressions
    def recursive(self, element):
        s = ""
        for e in element:
            name = str(e).split("'")[1].replace(self.edoal_namespace, "")
            if (self.process_simple_expression(name, e) != False):
                #simple expression
                s += self.process_simple_expression(name, e)
            else:
                #nested expression
                sub_const = str(e[0]).split("'")[1].replace(self.edoal_namespace, "")
                if (sub_const in self.construction):
                    s += "{}{{ ".format(sub_const).upper()
                    s += self.recursive(e[0])
                    s += "} "
        return s

    # This method processes simple expressions inside the constructor
    def process_simple_expression(self, name, element):
        s= ""
        # (Property and relation) Restrictions 
        if name in self.restriction1:
            s += name + " (" + self.recursive(element[0])

        # (Attribute) Restrictions 
        if name in self.restriction2:
            s+= name + "{"
            for e in element:
                e_name = str(e).split("'")[1].replace(self.edoal_namespace, "")
                if e_name == "onAttribute":
                    s += "onAttribute: " + self.recursive(e)
                    continue
                elif e_name == "class": 
                    s += ", class: " + e[0].get('{}about'.format(self.rdf_namespace))
                    continue
                elif e_name == "exists": 
                    s += ", class: " + self.recursive(e)
                    continue
                elif e_name == "comparator":
                    comparator = e.get('{}resource'.format(self.rdf_namespace))
                    s += ", comparator: " + str(comparator).split("#")[1]
                    continue
                elif e_name == "value" :
                    if e.text != None:
                        s += ", value: " + e.text
                    else:
                        if (e[0].tag == "{}Literal".format(self.edoal_namespace)):
                            s += ", value: " + e[0].get('{}string'.format(self.edoal_namespace))
                        if (e[0].tag == "{}Instance".format(self.edoal_namespace)):
                            s += ", value: " + e[0].get('{}about'.format(self.edoal_namespace)) 
                    continue
                elif e_name == "{http://knowledgeweb.semanticweb.org/heterogeneity/alignment#}datatype": 
                    s += ", datatype: " + e[0].get('{}about'.format(self.rdf_namespace))
                    continue
            s+= "}; "

        # Relations, Property and Classes
        if name in self.basic_elements:
            # Make sure it's not a nested expression
            if (len(list(element))<1):
                s += name + "({})".format(element.get('{}about'.format(self.rdf_namespace))) + "; "

        if len(s)>0: return s
        else: return False

    def get_type_aln(self, const1, const2, ent1_type, ent2_type):
        if (const1 == "-") and (const2 == "-") and (ent1_type not in self.restriction2) and (ent2_type not in self.restriction2):
            return "Simple"
        else:
            return "Complex"

    def get_labels(self, ont_path):
        tree = ET.parse(ont_path)
        root = tree.getroot()
        labels = {}

        for _element in root:
            entity = _element.get('{}about'.format(self.rdf_namespace))
            label = _element.find('{}label'.format(self.rdfs_namespace))
            if(label is not None):
                labels[entity] = label.text
        return labels
    
    def replace_labels(self, df, column_name, labels):
        l = []
        for i in df[column_name]:
            if i in labels:
                l.append(labels[i])
            else:
                l.append(i)

        df[column_name] = l
        return df

    def evaluate(self, df, ref_path, mode):
        # Mode: "full", "found", "missing"
        # Namespaces -> reference namespaces have a '#' attached to the end
        pref = Parser(False)
        ref_df = pref.extract_mappings(ref_path)
       
        #l = []
        #for i in ref_df['entity1']:
        #    l.append(i.replace('#','/'))

        #ref_df['entity1'] = l

        if(mode == "full"):
            evaluation = df.merge(ref_df, how='outer', on=['entity1', 'entity2'], suffixes = ["", "_ref"])
            evaluation.drop(axis=1, 
                            labels= ['ent1_type_ref','constructor1_ref','ent2_type_ref','constructor2_ref',
                             'type_of_alignment_ref', 'measure_ref'],
                           inplace=True)
            evaluation.fillna(" ", inplace=True)
            
        if(mode == "found"):
            evaluation = df.merge(ref_df, how='inner', on=['entity1', 'entity2'], suffixes = ["", "_ref"])
            evaluation = evaluation[['entity1', 'entity2','relation','relation_ref']]

        if(mode == "missing"):
            evaluation = ref_df.merge(df, how='left', on=['entity1', 'entity2'], suffixes = ["_ref", ""])
            found = evaluation.dropna()
            evaluation.drop(axis=0, labels=found.index, inplace=True)
            evaluation = evaluation[['ent1_type_ref','entity1','constructor1_ref','ent2_type_ref','entity2',
                        'constructor2_ref','type_of_alignment_ref','relation_ref']]

        return evaluation

    # This function returns the number of different mappings types that exist in the given alignment
    def check_mapping_types(self, df):
        return df.groupby(['ent1_type','ent2_type']).size().reset_index(name='Count')