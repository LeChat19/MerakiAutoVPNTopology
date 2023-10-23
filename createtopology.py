import json
import graphviz
from autovpntree import Node


def dynamicfont(x, limit=256):
    # We use  function to increase size depending on the children count.
    #Initial font size is 12
    initial_value = 12
    maxvalue = limit
    fontsize = 0.1*x + initial_value
    if fontsize <= maxvalue:
        return fontsize
    else:
        return maxvalue


def get_dictcs_from_json(filename):
    #Dicts from json files
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


def create_hublist(hubs):
    # Parsing json file created by API requests.
    # We add hubs first at the highest level.
    l_hubs = hubs
    l_hub_list = []
    l_root_list = []
    for key , value in l_hubs.items():
        l_hub_list.append(key)
        #Creating Node object.
        root = Node(key, type="hub", mxnames=value["name"], subnets=value["subnets"])
        l_root_list.append(root)
    return l_root_list


def add_spokes_to_tree(spokes, rootlist):
    # Adding spokes to the tree objects
    # We add them to the tree object
    l_spokes = spokes
    l_rootlist = rootlist
    for key , value in l_spokes.items():
        for record in l_rootlist:
            #Linkorder tells us priority of the link to hub.
            linkorder = 0
            for spokehub in value["hubs"][0]:
                linkorder += 1
                #We set linkorder maximum to 3. So we have 3 different colors and labales.
                if linkorder >= 3:
                    linkorder = 3
                if record.name == spokehub["hubId"]:
                    record.children.append(Node(key, type="spoke", order=linkorder,
                                                model=value["model"], mxnames=value["name"],
                                                subnets=value["subnets"]))
                    for spoke in record.findall(name=key):
                        for subnet in value["subnets"]:
                            spoke.children.append(Node(subnet["localSubnet"], type=subnet["useVpn"]))
    return l_rootlist


def subnetlabel(subnet):
    # Function to create labels for Subnets
    # We add all subnets which are marked to use VPN
    label=""
    for subrecord in subnet:
        if subrecord["useVpn"] == True:
            label += "|" + subrecord["localSubnet"]
    #removing leading |
    label = label[1:]

    return label


def convert_dict_to_hashable(d):
    # We use this function if we need to use spoke data
    # as unique indexes. It's used for summarizsaed topologies
    if isinstance(d, dict):
        # Convert the dictionary items to a list of tuples and sort them
        items = sorted((key, convert_dict_to_hashable(value)) for key, value in d.items())
        return tuple(items)
    elif isinstance(d, list):
        # Recursively convert list elements
        return tuple(convert_dict_to_hashable(item) for item in d)
    elif isinstance(d, set):
        # Convert sets to frozensets
        return frozenset(convert_dict_to_hashable(item) for item in d)
    else:
        # Other types are left as-is
        return d


def create_set(rootlist):
    # We create a set of tuples.
    # We want to find all combinations of hubs which
    # have at least one common spoke connected
    l_rootlist = rootlist
    hubset = set()
    dict_commonhubs = {}
    for hubs in l_rootlist:
        for child in hubs.children:
            if child.name in dict_commonhubs.keys():
                dict_commonhubs[child.name].append(hubs)
            else:
                dict_commonhubs[child.name] = [hubs]

    for values in dict_commonhubs.values():
        hubset.add(tuple(values))
    return(hubset)



def merge_spokes(spokes):
    # We use this function to create a merged dictionary
    # We create a hash based on value of spoke. Value is hubs it's connected to ,
    # model etc.
    s = {}
    spokes_merged = {}
    for spokekey, spokevalue in spokes.items():
        sublabel = []
        for subnet in spokevalue['subnets']:
            if subnet["useVpn"] == True:
                sublabel.append(subnet)


        s['hubs'] = spokevalue['hubs'][0]
        s['model'] = spokevalue['model']


        if convert_dict_to_hashable(s) in spokes_merged:
            spokes_merged[convert_dict_to_hashable(s)].append(sublabel)
        else:
            spokes_merged[convert_dict_to_hashable(s)] = [sublabel]


    return spokes_merged


def merge_spokes_spokename(spokes):
    # We use this function to create a merged dictionary
    # We create a hash based on value of spoke. Value is hubs it's connected to ,
    # model etc.
    #The difference is that we record spokenames instead of subnets in the list of values
    s = {}
    spokes_merged = {}
    for spokekey, spokevalue in spokes.items():

        s['hubs'] = spokevalue['hubs'][0]
        s['model'] = spokevalue['model']

        #if it exists we just add a name of spoke into the list
        #if it doesn't exist we create a new one.
        if convert_dict_to_hashable(s) in spokes_merged:
            spokes_merged[convert_dict_to_hashable(s)].append(spokekey)
        else:
            spokes_merged[convert_dict_to_hashable(s)] = [spokekey]

    return spokes_merged





def create_graph(root_list, networks, graphf):
    l_networks = networks
    nodes = []
    edges = []
    iternumber = 0
    listofsubnetlabels = []
    listofedges = []
    f = graphf


    for a in root_list:
        iternumber += 1

        f.node(a.name, label= l_networks[a.name] + "|" + a.type + "|" + a.mxnames + "|" + subnetlabel(a.subnets),
               shape="Mrecord", style="filled", fillcolor= "#33CAFF" )
        #f.node(a.name, label= a.name + "|" + a.type + "|" + a.mxnames + "|" + subnetlabel(a.subnets),
        #       shape="Mrecord", style="filled", fillcolor= "#33CAFF", )
        for b in a.children:
            f.node(b.name, label=l_networks[b.name] + "|" + b.type + "|" + b.model  + "|" +
                                 b.mxnames + "|" + subnetlabel(b.subnets),
                   shape="Mrecord", style="filled", fillcolor="#fbd7c6")
            #f.node(b.name, label=b.name + "|" + b.type + "|" + b.model + "|" +
            #                                          b.mxnames + "|" + subnetlabel(b.subnets),
            #                            shape="Mrecord", style="filled", fillcolor="#fbd7c6")
            subnetlabelvpn = ""
            subnetlabelnonvpn = ""
            for subnet in b.children:
                if subnet.type == "True":
                    subnetlabelvpn += subnet.name + " | "
                elif subnet.type == "False":
                    subnetlabelnonvpn += subnet.name + " | "
            f.edge(b.name, a.name, label=str(b.order), color=linecolormap[b.order - 1], fontcolor=linecolormap[b.order - 1])
            #if b.name + "vpn" not in listofsubnetlabels:
            if False == True:
                if subnetlabelvpn:
                        listofsubnetlabels.append(b.name + "vpn")
                        f.node(b.name + "vpn",  label = subnetlabelvpn, shape="Mrecord", style="filled", fillcolor="green")
                        f.edge( b.name + "vpn", b.name)
                if subnetlabelnonvpn:
                        f.node(b.name + "nonvpn",  label = subnetlabelnonvpn, shape="Mrecord", style="filled", fillcolor="red")
                        f.edge(b.name + "nonvpn", b.name, )
                listofsubnetlabels.append(b.name)
        if a.type == "hub":
            hub = a.name
        '''for child in a.getchildren():
            f.node(a.name, label=a.name + a.type)
            f.edge(child.name, hub)
            #print("children", iternumber, child.name, child.type, hub)'''





def create_invis_root(hubs, graphopject):
    # We need this function for twopi layout
    # We create an invisible node connected to hubs.
    # So it will be in a center.

    f = graphopject
    for hubname in hubs:
        linecolor =0
        f.node("central hub", style="invis")
        f.edge(hubname.name, "central hub", style="invis")
    return f

def create_graph_by_set(hubset, networks,
                        colortolabel, linecolormap,
                        graphopject, invisnode=True):
    l_networks = networks
    f = graphopject
    nodes = []
    edges = []
    iternumber = 0
    listofsubnetlabels = []
    listofedges = []
    hublist = list(hubset)
    hublistlen = len(hublist)
    #element = hublist[2]
    for element in hubset:
    #if True:
        if invisnode:
        #if hublistlen == 1:
            f = create_invis_root(element, f)
        for a in element:
            iternumber += 1
            f.node(a.name, label= l_networks[a.name] + "|" + a.type + "|" + a.mxnames + "|" + subnetlabel(a.subnets),
                   shape="Mrecord", style="filled", fillcolor= "#33CAFF" )
            for b in a.children:
                f.node(b.name, label=l_networks[b.name] + "|" + b.type + "|" + b.model  + "|" +
                                     b.mxnames + "|" + subnetlabel(b.subnets),
                       shape="Mrecord", style="filled", fillcolor="#fbd7c6")
                subnetlabelvpn = ""
                subnetlabelnonvpn = ""
                #need to check 0.0.0.0
                edgelabel = create_label(b.order, linecolormap, colortolabel, False)
                for subnet in b.children:
                    if subnet.type == "True":
                        subnetlabelvpn += subnet.name + " | "
                    elif subnet.type == "False":
                        subnetlabelnonvpn += subnet.name + " | "
                if [b.name, a.name] not in listofedges:
                    listofedges.append([b.name, a.name])
                    f.edge(b.name, a.name, label = edgelabel,
                           color=linecolormap[b.order - 1], fontcolor=linecolormap[b.order - 1])
    return f



def link_hub(spokes, hubs, networks,
             colortolabel, linecolormap,
             graphopject):
    l_networks = networks
    f = graphopject
    edgecount = 0
    hubcount = 0
    site_label = set()
    for hubkey, hubvalue in hubs.items():
        sublabel = ""
        sequence = 0
        for subnet in hubvalue['subnets']:
            if subnet["useVpn"] == True:
                sequence += 1
                sublabel += str(sequence) + ". " + str(subnet["localSubnet"]) + "|"
        hubcount += 1
        sublabel = sublabel[:len(sublabel) - 1]
        f.node(hubkey, label=  hubkey  + " | " +  hubvalue['model'] + " | " +  hubvalue['name']  + "|"  ,
                labelloc="c", shape="Mrecord", style="filled", color="black", fillcolor="#33CAFF")
        for spokekey, spokevalue in spokes.items():
            #we check every hub in tuple with sets
            linecolor = 0
            for record in spokekey[0][1]:
                linecolor +=1
                deflabel = ""
                if record[0][1] == hubkey:
                    edgecount += 1
                    #This f node is used if we want just caluclate count.
                    '''f.node(str(spokekey[0]) + "|" +
                           str(spokekey[1]) + "|" +
                           str(len(spokevalue)), label= str(spokekey[1][1]) + "| Spoke count: " +
                           str(len(spokevalue)) ,
                           labelloc="c", shape="Mrecord", style="filled", color="black", fillcolor="#fbd7c6")'''
                    # This f node is used if we want to see networks.
                    spokenetworks = ""
                    tennetinaraw = 0
                    for i in spokevalue:
                        if tennetinaraw != 9:
                            spokenetworks += l_networks[i] + " , "
                            #spokenetworks += i + " , "
                            tennetinaraw += 1
                        else:
                            tennetinaraw = 0
                            spokenetworks += l_networks[i] + "|"
                            #spokenetworks += i + "|"
                    f.node(str(spokekey[0]) + "|" +
                           str(spokekey[1]) + "|" +
                           str(len(spokevalue)), label= str(spokekey[1][1]) + "| Network count: " + str(len(spokevalue)) +  " names: |" +
                           str(spokenetworks) ,
                           labelloc="c", shape="Mrecord", style="filled", color="black", fillcolor="#fbd7c6")
                    f.node(hubkey, label=l_networks[hubkey] + " | " + hubvalue['model'] + " | " + hubvalue['name'] ,
                           labelloc="c", shape="Mrecord", style="filled", color="black", fillcolor="#33CAFF")
                    edgelabel = create_label(linecolor, linecolormap, colortolabel, record[1][1])
                    f.edge(str(spokekey[0]) + "|" +
                           str(spokekey[1]) + "|" +
                           str(len(spokevalue)), str(hubkey),
                           label = edgelabel,
                           color=linecolormap[linecolor - 1],
                           fontcolor=linecolormap[linecolor - 1])
    return f

def create_label(linecolor, linecolormap, colortolabel, defroute):
    #creating label for node or edge.
    deflabel = ""
    if defroute == True:
        deflabel = "0.0.0.0/0"
    label = deflabel + "\n" + colortolabel[linecolormap[linecolor - 1]]
    return label

