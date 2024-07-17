
from collections import defaultdict
from .plugin import Plugin

import re


umlauts = {"a": "ä", "o": "ö", "u": "ö", "å": "ä", "y" : "ö"}

umlauts_ö : {"å" : "ö","y" : "ö", "o" : "ö"}

delimiters = "%+="
vowels     = "aouåeiyäö"
alphabet   = "abcdefghijklmnopqrstuvwxyzåäö"

consonants = "".join([c for c in alphabet if c not in "aouåeiyäö"])


def fv(s):
    # if only one vowel - do not remove it
    if len([c for c in s if c in vowels]) <= 1:
        return s

    if s[-2] in "aeiouy":
        s = s[0:-2] + s[-1:]
        if s[-3:-1] == "mm":
            s = s[:-2] + s[-1]
    return s


# double final consonant
def dk(s):
    # special case for k
    if s[-1] == "k":
        s = s[0:-1] + "ck"
    elif is_consonant(s[-1]):
        s = s + s[-1]
    return s

def ek(s):
    
     for i in reversed(range(0, len(s) - 1)):
       
        if s[i + 1] in "mnr" and s[i + 1] == s[i]:
           
            # found doubled m,n or r
            s = drop_index(i, s)
            break
         #   print(s)
        elif is_consonant(s[i+1]) : 
          
            ()
        
             
     return s


def om(s,dct):
    for i in reversed(range(0, len(s))):
        if s[i] in dct:
            s = s[0:i] + dct[s[i]] + s[i + 1 :]
            break
    return s



def tj(s):
    for i in reversed(range(0, len(s))):
        if s[i] == "g":
            s = s[0:i] + "gj" + s[i + 1 :]
            break
    return s


#%ej - finds last occurrence of 'gju' or 'skju' or 'stjä' and removes j from it
def ej(s):
    drop_j = {"gju": "gu", "skju": "sku", "stjä": "stä"}
    for i in reversed(range(0, len(s) - 2)):
        for st in drop_j.keys():
            if s[i:].startswith(st):
                s = s[0:i] + drop_j[st] + s[i-1 + len(st) + 1 :]
                break
    return s

def asc(s) : 
    if s[-1] in "sxzSXZ" :
        return s
    else : return s + "s"
    
def ascc(s) : 
   # print(s)
    if s[-1] in "sxzSXZ" :
        return s
    else : return s + ":s"
    
def is_vowel(c):
    return c in vowels

def is_consonant(c):
    return c in consonants


def always(c):
    return True
    
def remove_last(cond, s):
    if cond(s[-1]):
        return s[:-1]
    else:
        return s

def drop_index(i, s):
    if i == 0:
        return s[1:]
    elif i == -1:
        return s[0:i]
    else:
        return s[0:i] + s[i + 1 :]


def replace_last_vowel(s, c):
    for i in reversed(range(0, len(s))):
        if s[i] in vowels:
            s = s[0:i] + c + s[i + 1 :]
            break
    return s

rules = {
    "%sp": lambda s: remove_last(always, s),
    "%sk": lambda s: remove_last(is_consonant, s),
    "%sv": lambda s: remove_last(is_vowel, s),
    "%ts": lambda s: remove_last(always, remove_last(always, s)),
    "%ss": lambda s: remove_last(lambda x: x == "s", s),
    "%fv": fv,  # remove last vowel if in [aeiou], make preceding double m single
    # (rymmas -> ryms, skrämmas -> skräms)
    "%dk": dk,  # double consonant
    "%ek": ek,  # make double consonant single
    "%om": lambda s : om(s,umlauts),  # umlaut on last occurrence of aouå
    "%avö": lambda s : om(s,umlauts_ö),
    "%tj": tj,  # last occurrence of g -> gj
    "%ej": ej,  # remove j from last occurrence of "skju", "gju" and "stjä"
    "%asc" :asc, # add "s" if stem does not end with s,x or z.
    "%ascc" : ascc # # add ":s" if stem does not end with s,x or z.
}

# precondition:
# rules != "" and rules always contain at least one delimiter symbol
def get_first_step(rules):
    delims = [symbol for symbol in rules if symbol in delimiters]
    if not delims : 
        return rules,""
        
    if len(delims) == 1:
        return rules, ""
    elif rules[0] == "=":
        return "=", rules[1:]
    else:
        # the start position of the next rule
        pos = re.match("[" + delimiters + "]" "[^" + delimiters + "]+", rules).end()
        return rules[0:pos], rules[pos:]

def apply_rule(rule, s):
    if not [c for c in rule if c in delimiters] :
        return rule
    if rule == "=":
        return s

    elif rule.startswith("+"):
         
        return s + rule[1:].replace("/", "")
    elif rule.startswith("%av"):
        return replace_last_vowel(s, rule[3])
    else:
        return rules[rule](s)

def apply_rules(s,rules):
    
    if rules != "":
        step, remainder = get_first_step(rules)
        new_s = apply_rule(step, s)
        return apply_rules(new_s,remainder)
    else:
        return s


class InflectionPlugin(Plugin):
    def output_config(self):  # noqa
        config = {"collection" : True,
                 "type" : "object",
                 "fields" : { "heading" : {"type" : "string"},  
                              
                              "rows" :    { "collection" : True, 
                                            "type" : "object", 
                                            "fields" : {
                                                
                                                "linenumber" : {"type" : "number"},
                                                         
                                                "row" : {
                                                          "type" : "object",
                                                          "fields" : {"preform" : {"collection" : True, 
                                                                                   "type" : "object",
                                                                                   "fields" : 
                                                                                              {"prescript" : {"type" : "string"},
                                                                                               "form" : {"type" : "string"},
                                                                                               "tag" : {"type" : "string"}
                                                                                              }
                                                                                               
                                                                                          },
                                                                      "postscript" : {"type" : "string"},
                                                                      "extra" : {"type" : "string"}
                                                                 }}
                                                                                                                                          
                                                        }        
                                            }
                                }
                }
                

        return config


    def generate(self, lemma, table):
        
        definitioner = table['definition']
        tabellrader = defaultdict(list)
         
        for defi in definitioner : 
            if defi['prescript'] is None : 
                raise 
            rownr = defi['row']
            rules = defi['rules']
           
            inflected_form = apply_rules(lemma,rules)
            heading = defi['heading']
            
            if tabellrader[heading] and tabellrader[heading][-1]['linenumber'] == rownr :
                
                last_row = tabellrader[heading].pop()         
                last_row['preform'].append((defi['prescript'],inflected_form,defi['tagg']))
                tabellrader[heading].append(last_row)
                        
            else :     
                tabellrader[heading].append({'preform' : [(defi['prescript'],inflected_form,defi['tagg'])],
                                            'postscript' : defi['postscript'], 
                                            'extra' : defi['extra'],
                                            'linenumber' : rownr}) 
        the_result = []
        
        for heading in tabellrader.keys() : 
            
            heading_rows = tabellrader[heading]
            rows = []
            for hr in heading_rows : 
                
               
               linenumber = hr['linenumber']
               
               preforms = []
               preforms_hr = hr['preform']
               
               if hr['preform'] is None : 
                   raise Exception(tabellrader) 
               
               for pf in preforms_hr : 
                   
                   if not type(pf) is tuple : 
                       raise Exception(preforms,pf,type(pf))
                       
                   preforms.append({'prescript' : pf[0], 'form' : pf[1] , 'tag' : pf[2] })
               
                   
               row = { 'linenumber' :  hr['linenumber'],
                       'row' : {   'preform' : preforms,
                                   'postscript' : hr['postscript'],
                                   'extra' : hr['extra']
                                }
                      }
 
               rows.append(row)
                
            
            obj = {"heading" : heading,
                   "rows" : rows}
                   
            the_result.append(obj)
        
        return the_result
                    