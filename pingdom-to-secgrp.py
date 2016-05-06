import feedparser
from incf.countryutils import transformations
import argparse
import boto3

URL = "https://my.pingdom.com/probes/feed"

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vpcid", action="store", dest="vpcid", required=True)
parser.add_argument("-p", "--port", action="store", dest="port", required=True, type=int)
args = parser.parse_args()

conn = boto3.client('ec2')

def get_pingdom_probes(url):
	response = feedparser.parse(url)

	probes = []

	for item in response['items']:
		if item['pingdom_state'] == "Active":
			#Hack because Pingdom uses UK not GB for the country code alpha
			if item['pingdom_country']['code'] == "UK":
				probe = {
					"ip": item['pingdom_ip'],
					"region": "Europe"
				}

				probes.append(probe)
			else:
				probe = {
					"ip": item['pingdom_ip'],
					"region": transformations.cca_to_ctn(item['pingdom_country']['code'])
				}

				probes.append(probe)

	return probes

#create secgrp
def create_security_group(conn, vpcid, port, probes):
	pingdom_north_america_sec_grp = ec2.create_security_group(GroupName="pingdom_north_america_sec_grp", VpcId=vpcid, Description="Pingdom North America probe IPs")
    pingdom_europe_sec_grp = ec2.create_security_group(GroupName="pingdom_europe_sec_grp", VpcId=vpcid, Description="Pingdom Europe probe IPs")
    pingdom_asia_pacific_sec_grp = ec2.create_security_group(GroupName="pingdom_asia_pacific_sec_grp", VpcId=vpcid, Description="Pingdom Asia Pacific probe IPs")
    
    for probe in probes:
    	if probe['region'] == "North America":
    		pingdom_north_america_sec_grp.authorize_ingress(IpProtocol="tcp",CidrIp=probe + "/32",FromPort=port,ToPort=port)
    	elif probe['region'] == "Europe":
    		pingdom_europe_sec_grp.authorize_ingress(IpProtocol="tcp",CidrIp=probe + "/32",FromPort=port,ToPort=port)
    	else:
    		pingdom_asia_pacific_sec_grp.authorize_ingress(IpProtocol="tcp",CidrIp=probe + "/32",FromPort=port,ToPort=port)

    return

probes = get_pingdom_probes(URL)

create_security_group(conn, args.vpcid, args.port, probes)