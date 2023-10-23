import meraki
import json
import sys
from rich import print as pp
from rich.console import Console
from rich.table import Table
import os
from getpass import getpass





def ensure_directory_exists(directory_path):
    """
    Check if a directory exists. If not, create it.

    Args:
    - directory_path (str): The path of the directory to check/create.
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Directory created: {directory_path}")
        except OSError as e:
            print(f"Error creating directory {directory_path}: {e}")


#Oren Brigg code to select org.
def select_org(client):
    l_client = client
    # Fetch and select the organization
    print("\n\nFetching organizations...\n")
    try:
        organizations = l_client.organizations.getOrganizations()
    except Exception as e:
        pp(f"[red]An error has occured: \n\n{e}[/red]\n\nExiting...")
        pp("A newly generated API key will require up to 15 minutes to synchronize with Meraki API gateways. \
            \nIf you're using a new key - kindly try again in a few minutes.")
        sys.exit(1)
    organizations.sort(key=lambda x: x["name"])
    ids = []
    table = Table(title="Meraki Organizations")
    table.add_column("Organization #", justify="left", style="cyan", no_wrap=True)
    table.add_column("Org Name", justify="left", style="cyan", no_wrap=True)
    counter = 0
    for organization in organizations:
        ids.append(organization["id"])
        table.add_row(str(counter), organization["name"])
        counter += 1
    console = Console()
    console.print(table)
    isOrgDone = False
    while isOrgDone == False:
        selected = input(
            "\nKindly select the organization ID you would like to query: "
        )
        try:
            if int(selected) in range(0, counter):
                isOrgDone = True
            else:
                print("\t[red]Invalid Organization Number\n")
        except:
            print("\t[red]Invalid Organization Number\n")
    return (organizations[int(selected)]["id"], organizations[int(selected)]["name"])


#Get all Networks for the ogranization. We need them to replace id to a name.
def get_networks(orgid, client):
    l_networkdict = {}
    #Create networks dictionary. ID is the key, Name is the value
    perPagevalue = 1000
    l_networks = []
    try:
        l_networks_page = client.organizations.getOrganizationNetworks (orgid, perPage=perPagevalue, total_pages="all")
        #print(l_networks_page)
        l_networks += l_networks_page
    except Exception as e:
        pp(f"[bold magenta]Some other ERROR: {e}")
        isDone = True
    for i in l_networks:
        l_networkdict[i["id"]] = i["name"]
    return l_networkdict

#We get a list of devices and site to site VPN data for
# networks
def get_devices(orgid, client):
    ## We get only appliances by using productTypes='appliance'.
    perPagevalue=1000
    startingAfter = ''
    l_devices = []
    try:
        l_devices_page = client.organizations.getOrganizationDevices (
            orgid, productTypes='appliance',
            perPage=perPagevalue, total_pages="all")
        #print(l_devices_page)
        l_devices += l_devices_page
        #if len(l_devices_page) < perPagevalue:
        #    isDone = True
        #else:
        #    startingAfter = l_devices_page[perPagevalue - 1]['serial']
        #    #print("startingAfter devices", startingAfter)
    except Exception as e:
        pp(f"[bold magenta]Some other ERROR: {e}")

    l_spokes={}
    l_hubs={}
    for i in l_devices:
        #We get configuration of applinces for site to site.
        l_sitetositeVPN = (
            "sitetositeVPN",
            client.appliance.getNetworkApplianceVpnSiteToSiteVpn(i['networkId']))
        #If it's a hub
        if l_sitetositeVPN[1]['mode'] == 'hub':
            #If network is already in dict it means that this is a pair of devices
            if i['networkId'] in l_hubs:
                l_hubs[i['networkId']]['name'] = l_hubs[i['networkId']]['name'] + "|" + i['name']
            #New network and device
            else:
                l_hubs[i['networkId']] = {"model": i['model'], "mode": l_sitetositeVPN[1]['mode'],
                                        "name": i['name'], "subnets": l_sitetositeVPN[1]["subnets"]}
        #Or spoke
        elif l_sitetositeVPN[1]['mode'] == 'spoke':
            # If network is already in dict it means that this is a pair of devices
            if i['networkId'] in l_spokes:
                l_spokes[i['networkId']]['name'] : {l_spokes[i['networkId']]['name']
                                                  + i['name']}
            # New network and device
            else:
                l_spokes[i['networkId']] = {"model": i['model'], "mode": l_sitetositeVPN[1]['mode'], "name": i['name']
                    , "hubs": [l_sitetositeVPN[1]["hubs"]], "subnets": l_sitetositeVPN[1]["subnets"]}
    return(l_spokes, l_hubs)

def gooverorgs(orgid, client, directory ):
    networkdict = get_networks(orgid, client)
    spokes, hubs = get_devices(orgid, client)

    def dict_to_json(my_variable, filename):
        with open(directory + filename + '.json', 'w') as fp:
            json.dump(my_variable, fp)


    dict_to_json(networkdict, "networkdict" + orgid)
    dict_to_json(hubs, "hubs" + orgid)
    dict_to_json(spokes, "spokes" + orgid)


def check_files_exist(orgid, directjson=""):
    """
    Check if files from the given list exist locally.
    We need orgid to check for local files
    """
    print(directjson)
    file_list = [directjson + "networkdict" + orgid + ".json",
                 directjson + "hubs" + orgid + ".json",
                 directjson + "spokes" + orgid + ".json"]
    existinfiles = []

    print(file_list)

    for file_path in file_list:
        if os.path.exists(file_path):
            existinfiles.append(file_path)

    return existinfiles

def make_files():
    '''Main function which will run APIs and create local files if user slects to create new ones.
    We have to run 1 request per appliance pair in a network. So if we have for example 1000+ branches it will send 1000+ requests
    '''
    params = {}
    directory_path = "datajson/"
    output_path = "output/"


    # Check for an envriomnet variable, if not set, ask for an API key
    if os.environ.get("MERAKI_DASHBOARD_API_KEY"):
        api_key = os.environ["MERAKI_DASHBOARD_API_KEY"]
    else:
        pp(
            "[bold magenta]No API key found. Please enter your Meraki Dashboard API key:"
        )
        api_key = getpass("Meraki Dashboard API Key: ")
        os.environ["MERAKI_DASHBOARD_API_KEY"] = api_key


    client = meraki.DashboardAPI(output_log=True, suppress_logging=False, maximum_retries= 50, caller='topology build/apiskuno')
    orid, orname = select_org(client)
    params["organization_id"] = orid
    params["organization_name"] = orname
    #We check for local files based on org id.
    localfiles = (check_files_exist(params["organization_id"], directory_path))
    print(localfiles)
    isLocalFiles = False
    ensure_directory_exists(directory_path)
    ensure_directory_exists(output_path)


    if len(localfiles) == 3:
        while isLocalFiles == False:
            print("You have files locally for your org id: ", orname)
            for file in localfiles:
                print(file)
            selected = input(
                "\nDo you want to use these files (Y) or get Data from Dashboard (N) ? "
                "\n Select Y/N"
            )
            if str(selected).lower() == 'y':
                isLocalFiles = True
            elif str(selected).lower() == 'n':
                gooverorgs(orid, client, directory_path)
                isLocalFiles = True
            else:
                print("\t[red]Invalid input. Select Y/N\n")
    else:
        gooverorgs(orid, client, directory_path)
    return params["organization_id"], params["organization_name"]


if __name__ == "__main__":
    make_files()




