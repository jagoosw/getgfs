import requests,json,os,re
import pandas as pd
from datetime import date

route=os.path.abspath(os.path.dirname(__file__))

url="https://nomads.ncep.noaa.gov/dods/gfs_{res}{step}/gfs{date}/gfs_{res}{step}_{hour:02d}z.{info}"
config_file="%s/config.json"%route
attribute_file="%s/atts/{res}{step}.json"%route

if not os.path.isdir("%s/atts"%route):
    os.makedirs("%s/atts"%route)
if not os.path.isfile(config_file):
    with open(config_file,"w+") as f:
        json.dump({"saved_atts":["Na"]},f)
class Forcast:
    def __init__(self,resolution, timestep=""):
        if timestep!="":
            timestep="_"+timestep
        self.resolution=resolution
        self.timestep=timestep
        self.times,self.coords,self.variables=get_attributes(resolution,timestep)

def get_attributes(res,step):
    with open(config_file) as f:
        config=json.load(f)
    if "{res}{step}".format(res=res,step=step) not in config["saved_atts"]:
        r=requests.get(url.format(res=res,step=step,date=date.today().strftime("%Y%m%d"),hour=0,info="das"))
        if r.status_code!=200:
            raise Exception("The forcast resolution and timestep was not found")
        search_text=re.sub("\s{2,}","",r.text[12:-2])
        raws=re.findall(r"(.*?) \{(.*?)\}",search_text)
        variables={}
        coords={}
        for var in raws:
            attributes={}
            atts=var[1].split(";")
            #Extraction from a line could be simplified to a function
            if var[0] not in ["time","lat","lon","lev"]:
                for att in atts:
                    iden,val=extract_line(["_FillValue","missing_value","long_name"],att)
                    if iden!=None:
                        attributes[iden]=val
                variables[var[0]]=attributes
            elif var[0]=="time":
                for att in atts:
                    iden,val=extract_line(["grads_size","grads_step"],att)
                    if iden!=None:
                        attributes[iden]=val
                time=attributes
            else:
                for att in atts:
                    iden,val=extract_line(["grads_dim","grads_size","minimum","maximum","resolution"],att)
                    if iden!=None:
                        attributes[iden]=val
                coords[var[0]]=attributes
        
        r=requests.get(url.format(res=res,step=step,date=date.today().strftime("%Y%m%d"),hour=0,info="dds"))
        if r.status_code!=200:
            raise Exception("The forcast resolution and timestep was not found")
        arrays=re.findall(r"ARRAY:\n(.*?)\n",r.text)
        for array in arrays:
            var=re.findall(r"(.*?)\[",array)[0].split()[1]
            if var in variables.keys():
                lev_dep=False
                for dim in re.findall(r"(.*?)\[",array):
                    if dim.split()[0]=="lev":
                        lev_dep=True
                variables[var]["level_dependent"]=lev_dep

        save={"time":time,"coords":coords,"variables":variables}
        with open(attribute_file.format(res=res,step=step),"w+") as f:
            json.dump(save,f)
        config["saved_atts"].append("{res}{step}".format(res=res,step=step))
        with open(config_file,"w+") as f:
            json.dump(config,f)
        return time,coords,variables
    else:
        with open(attribute_file.format(res=res,step=step)) as f:
            data=json.load(f)
        return data["time"],data["coords"],data["variables"]

def extract_line(possibles,line):
    found=-1
    ind=-1
    while (found==-1 and ind<len(possibles)-1):
        ind+=1
        found=line.find(possibles[ind])
    
    if found!=-1:
        if line[0:3]=="Str":
            return possibles[ind], line[found+len(possibles[ind])+2:-1]
        elif line[0:3]=="Flo":
            return possibles[ind], float(line[found+len(possibles[ind])+1:])
    return None,None
    
    
test=True
f=Forcast("0p25")
print(f.coords)
if test==True:
    os.remove(config_file)
    import shutil
    shutil.rmtree("%s/atts"%route)