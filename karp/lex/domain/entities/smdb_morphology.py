
import sys
import sqlalchemy as db
import re

from typing import Any

from karp.lex.domain.entities import Morphology


umlauts    = {'a':'ä','o':'ö','u':'ö','å':'ä'}    
delimiters = "%+="   
vowels     = "aouåeiyäö"
alphabet   = "abcdefghijklmnopqrstuvwxyzåäö"
    
consonants = ''.join([c for c in alphabet if c not in "aouåeiyäö"])
    
        
class SmdbMorphology(Morphology) :
    

    def get_inflection_table(self,identifier : str,lemma : str, **kwargs) -> list[dict[str, Any]]:
        
        # fetch rows with identifier in inflection database
        # apply rules to lemma and return dict with word forms
        
        engine      = db.create_engine('mysql://root@localhost/morphology')
        connection  = engine.connect()
        metadata    = db.MetaData()
        table       = db.Table('inflection_table', metadata, autoload=True, autoload_with=engine)
        query = db.select([table]).where(table.columns.bklass == identifier)
        
        ResultProxy = connection.execute(query)
        ResultSet = ResultProxy.fetchall()
        
        inflections = {}
        
        for (n,ident,form,rule) in ResultSet :
            inflections[form] = apply_rules(rule,lemma)
            
  #      print(inflections)
        return inflections
        

def apply_rule(rule,s) :
        if rule == '=' :
            return s
        elif rule.startswith('+') :
            return s + rule[1:].replace('/','')
        elif rule.startswith('%av') :
            return replace_last_vowel(s,rule[3])
        else : return rules[rule](s)
    
    
def apply_rules(rules,s) :
        
        if rules != "" :
            step,remainder = get_first_step(rules)
           
            new_s = apply_rule(step,s)
         
            return apply_rules(remainder,new_s)
        else :
            return s
            
           
    # precondition: 
    # rules != "" and rules always contain at least one delimiter symbol
def get_first_step(rules) : 
        delims = [symbol for symbol in rules if symbol in delimiters]
        if len(delims) == 1 :
            return rules,""
        elif rules[0] == '=' : 
            return '=',rules[1:]
        else : 
            # the start position of the next rule
            pos = re.match('['+delimiters+']''[^' + delimiters +  ']+' ,rules).end()        
            return rules[0:pos],rules[pos:]  
  
           
def fv(s) :
        # if only one vowel - do not remove it
        if len([c for c in s if c in vowels]) <= 1 :
            return s
   
        if s[-2] in "aeiouy" :
            s = s[0:-2] + s[-1:]
            if s[-3:-1] == 'mm' :
                s = s[:-2] + s[-1]
        return s

    # double final consonant
def dk(s) :
        # special case for k
        if s[-1] == "k" : 
            s = s[0:-1] + "ck"
        elif is_consonant(s[-1]) :
            s = s + s[-1]
        return s

    # TODO: should not undouble n in "bannlyst"...
def ek(s) : 
        for i in reversed(range(0,len(s)-1)) :
            if s[i+1] in "mnr" and s[i+1] == s[i] :   
                # found doubled m,n or r
                s = drop_index(i,s)
                break       
        return s

def om(s) :
        for i in reversed(range(0,len(s))) :
            if s[i] in umlauts :
                s = s[0:i] + umlauts[s[i]] + s[i+1:]
                break
        return s

def tj(s) :
        for i in reversed(range(0,len(s))) :
            if s[i] == 'g' :
                s = s[0:i] + "gj" + s[i+1:]
                break
        return s

drop_j = {'gju' : 'gu',
          'skju' : 'sku',
          'stjä' : 'stä'}

    
    
    #%ej - finds last occurrence of 'gju' or 'skju' or 'stjä' and removes j from it
def ej(s) :
        for i in reversed(range(0,len(s)-2)) :
            for st in drop_j.keys() :
                if s[i:].startswith(st) :
                    s = s[0:i] + drop_j[st] + s[i+len(st)+1:] 
                    break
        return s
    

def is_vowel(c) : 
        return c in vowels
def is_consonant(c) :
        return c in consonants

def always(c) :
        return True

def remove_last(cond,s) :
        if cond(s[-1]) :        
            return s[:-1]
        else :
            return s
    
def drop_index(i,s) :
        if i == 0 : 
            return s[1:]
        elif i == -1 :  
            return s[0:i]
        else : 
            return s[0:i] + s[i+1:]
    
def replace_last_vowel(s,c) :
        for i in reversed(range(0,len(s))) :
            if s[i] in vowels :
                s = s[0:i] + c + s[i+1:]
                break
        return s
        
rules = {"%sp"  : lambda s : remove_last(always,s),
             "%sk"  : lambda s : remove_last(is_consonant,s) ,
             "%sv"  : lambda s : remove_last(is_vowel,s),
             "%ts"  : lambda s : remove_last(always,remove_last(always(s))),
             "%fv"  : fv, # remove last vowel if in [aeiou], make preceding double m single
                          # (rymmas -> ryms, skrämmas -> skräms)
             "%dk"  : dk, # double consonant
             "%ek"  : ek, # make double consonant single
             "%om"  : om, # umlaut on last occurrence of aouå
             "%tj"  : tj, # last occurrence of g -> gj
             "%ej"  : ej  # remove j from last occurrence of "skju", "gju" and "stjä"
        }
    


