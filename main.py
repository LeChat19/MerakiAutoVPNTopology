import graphviz
from createjsonfiles import make_files
from createtopology import get_dictcs_from_json, create_hublist , \
    add_spokes_to_tree, create_set, merge_spokes_spokename, \
    link_hub, create_graph_by_set


def jsonfromfiles(prefixes, org, path):
    #we create a list with  json data based on orgid
    # and a list of prefixes. They are
    # fileprefixes = ["networkdict", "hubs", "spokes"]
    jsondata = {}
    for i in prefixes:
        jsondata[i] = get_dictcs_from_json(path + i + org + ".json")

    return jsondata

def create_graphobj(layout="dot", filename="topology", maintext = ""):
    #It's grapviz object.
    f = graphviz.Digraph('Site to Site VPN Topology', filename=filename + 'gv',   format='pdf')
    f.attr(rankdir='LR', size='8,5')
    f.attr(ranksep='1.0',nodesep='1.0')
    f.attr(resolution='1440')
    f.attr('node', shape='box')
    f.attr(label='Site to Site VPN Topology ' + maintext, labelloc="tr")
    f.attr(overlap='scale')
    f.attr(layout=layout)
    #f.attr(strict="true")
    #f.attr(ranksep="1.2")
    #f.attr(overlap_scaling="prism")
    #Imprtant to set scale to be round
    #f.attr(ratio="auto")
    #f.attr(root="central hub")

    #f.attr(fixedsize='false')
    #f.attr(voro_margin="true")
    return f


if __name__ == "__main__":
    orgname = "NO ORGNAME FOUND"
    orgid, orgname = make_files()



    #colors used for edge colors and labaling based on priority
    linecolormap = ["blue", "red", "green"]
    colortolabel = {"blue": "Primary link", "red": "Secondary link", "green": "Rest priorities"}
    #Output directory
    output_path = "output/"
    #json file directory
    datapath = "datajson/"

    fileprefixes = ["networkdict", "hubs", "spokes"]
    #Dictionary from json files
    jsonlist = jsonfromfiles(fileprefixes, orgid, datapath)

    #we creating and adding hubs and spokes to the tree
    g_rootlist = create_hublist(jsonlist["hubs"])
    g_rootlist = add_spokes_to_tree(jsonlist["spokes"], g_rootlist)

    #We create a hubset. It's a set of hub combination.
    # Each hub combination is unique.
    # We create it based on hub children combinations
    hubset =  create_set(g_rootlist)



    #merged_spokes=merge_spokes(g_spokes)
    merged_spokes = merge_spokes_spokename(jsonlist["spokes"])

    #It's a basic layout for graphviz i nour case. Another one is twopi for bigger graphs
    layout="dot"

    #create graphviz object
    mergedgraph = create_graphobj(layout, maintext=" MERGED for organizanion " + orgname)


    mergedgraph = link_hub(merged_spokes, jsonlist["hubs"], jsonlist["networkdict"], colortolabel, linecolormap, mergedgraph)

    counter = 0
    setofhubs = set()
    #Create full topology
    if len(jsonlist["spokes"]) > 40:
        layout = "twopi"
    f = create_graphobj(layout, maintext=" for organizanion " + orgname)
    create_graph_by_set(hubset, jsonlist["networkdict"], colortolabel,
                        linecolormap, f, invisnode=False)
    f.render(output_path + "topology_" + orgname)


    #creeate separate files per pairs.
    hubsettext = ""
    for element in hubset:
        hubsettext = ""
        for onehub in element:
            hubsettext += jsonlist["networkdict"][onehub.name] + " ,"
        hubsettext = hubsettext[:-2]
        grobjperhub = create_graphobj(layout, maintext=hubsettext)
        grobjperhub = create_graph_by_set([element], jsonlist["networkdict"],
                            colortolabel, linecolormap, grobjperhub)
        grobjperhub.render(output_path + "topology_per_common_hub" + hubsettext)


    mergedgraph.render(output_path + "merged_" +orgname)
