import re
from .plugin import Plugin
class ValencyPlugin(Plugin):
  

  def cleanup(self,input):
      input = re.sub(r"  +", " ", input)      # "    "  -->  " "
      input = re.sub(r" \] ?", r"] ", input)  # "[caps någon ]enar"  -->  "[caps någon] enar"
      input = re.sub(r" ?/ ?", "/", input)    # "någon /några" --> någon/några"
      return input


  def expand(self,s):
      if (m := re.search(r"\(([^\(\)\[\]]+)\)", s)):  # find "(...)", with no parentheses inside
          lpar, rpar = "{#", "#}"  # replace "(...)" by "{#...#}", to denote that it has been expanded
          mid_variants = [m[1]]
      elif (m := re.search(r"\[(\w+) ([^\(\)\[\]]+)\]", s)):  # find "[...]", with no parentheses inside
          lpar, rpar = "{%"+m[1]+"_", "%}"  # replace "[caps ...]" by "{%caps_...%}", to denote that it has been expanded
          mid_variants = [m[2]]
      elif (m := re.search(r"[^ \(\)\[\]]+/[^ \(\)\[\]]+", s)):  # find ".../.../...", with no parentheses or whitespace
          lpar, rpar = "", ""
          mid_variants = m[0].split("/")  # this removes all "/" inside the expanded string
      else:
          yield s
          return
      pre, post = s[:m.start()], s[m.end():]
      for mid in mid_variants:
          for exp_mid in self.expand(mid):
              # replace all " " by "_" do denote that this the mid string is expanded
              yield from self.expand(pre + lpar + exp_mid.replace(" ", "_") + rpar + post)
  
  def output_config(self):  # noqa
      config = {
          "collection": True,
          "type": "object",
          "fields": {
            "exp_valens" : {"type" : "string"}
          },
          "cache_plugin_expansion": False,
      }
      return config
      
      
      
  def generate(self,valens):
      print(valens)
      val = self.cleanup(valens)
      # this turns "[caps (]" into "(", and the same for ")": necessary to handle matched parentheses
      val = re.sub(r"\[caps ([\(\)])\]", r"\1", val)
      expansions = []
      for exp in self.expand(val):
          # replace back all temporary symbols
          exp = exp.replace("{#", "(").replace("#}", ")").replace("{%", "[").replace("%}", "]").replace("_", " ")
          # this turns "(" and ")" back into "[caps (]"
          exp = re.sub(r"([\(\)])", r"[caps \1]", exp)
          if not valens == exp : 
            expansions.append({"exp_valens" : exp})
#      print(expansions)
      return expansions
    
    
