# Meraki Auto VPN Topology 

This script visualises topology for Meraki AUTO VPN. The script uses The Meraki Dashboard API Python library to get data. It draws topologies using graphviz.

## Setup

Use requirements file to install python libraries. 

    pip install -r requirements.txt

You also need to install binaries for graphviz. Please follow instructions in this link 

https://pygraphviz.github.io/documentation/stable/install.html

## Usage

You'll need to provide Meraki Dashboard API to pull the data. You have different options to do it:

1. Export your API key as an [environment variable](https://www.twilio.com/blog/2017/01/how-to-set-environment-variables.html), for example:

    ```shell
    export MERAKI_DASHBOARD_API_KEY=YOUR_KEY_HERE
    ```
2. Script will ask you for API key if it's not defined as an environmental variable or in the code. Just copy/paste it and hit enter.
3. Alternatively, define your API key as a variable in your source code; this method is not recommended due to its inherent insecurity.

Run the script. 

    python main.py

Script will create output and datajson directories. Output will store topology outputs in pdf format and graphviz files. Datajson stores infirmation which was pulled from the Dashboard API. 

### Examples

You can find examples in pdf format in the examples folder.

<img src="https://github.com/LeChat19/MerakiAutoVPNTopology/blob/master/examples/topology_Meraki%20Launchpad%F0%9F%9A%80.png">~~~~