import datetime
import socket
import asyncio
import time
import random
import json
import boto3
import botocore
from botocore.config import Config

from walkoff_app_sdk.app_base import AppBase

def datetime_handler(x):
    """ This function is used make datetime object json serilizable, 
    removing this function can cause error in some actions """

    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

class AWSEC2(AppBase):
    __version__ = "1.0.0"
    app_name = "AWS ec2"  

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def auth_ec2(self, access_key, secret_key, region):
        my_config = Config(
            region_name = region,
            signature_version = 'v4',
            retries = {
                'max_attempts': 10,
                'mode': 'standard'
            },
        )

        self.ec2 = boto3.resource(
            'ec2', 
            config = my_config, 
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key,
        )

        return self.ec2

    # Write your data inside this function
    def get_rules(self, access_key, secret_key, region, NetworkAclId):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)

        network_acl = self.ec2.NetworkAcl(NetworkAclId)
        return network_acl.entries

    # Write your data inside this function
    def block_ip(self, access_key, secret_key, region, NetworkAclId, ip, direction):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        network_acl = self.ec2.NetworkAcl(NetworkAclId)

        if "/" not in ip:
            ip = f"{ip}/32"

        egress = direction != "inbound"
        # This is a shitty system :)
        minimum = 100
        max_range = 30000
        numbers = []
        #found = False
        for item in network_acl.entries:
            if egress != item["Egress"]:
                continue

            if ip == item["CidrBlock"]:
                raise Exception(f"IP {ip} is already being blocked.")

            numbers.append(item["RuleNumber"])


        for index in range(minimum, max_range):
            if index in numbers:
                continue

            minimum = index
            break

        print("New number: %d" % minimum)

        try:
            return network_acl.create_entry(
                CidrBlock = ip,
                DryRun = False,
                Egress = egress,
                IcmpTypeCode = {
                    'Code': 123,
                    'Type': 123
                },
                PortRange = {
                    'From': 0,
                    'To': 65535
                },
                Protocol = "6",
                RuleAction = "DENY",
                RuleNumber = minimum,
            )
        except botocore.exceptions.ClientError as e:
            print(f"Error: {e}")
            return f"{e}"


    # Write your data inside this function
    def create_acl_entry(self, access_key, secret_key, region, NetworkAclId , cidr_block, dryrun, direction, portrange_from, portrange_to, protocol, rule_action, rule_number):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)

        network_acl = self.ec2.NetworkAcl(NetworkAclId)
        if protocol.lower() == "tcp":
            protocol = "6"
        elif protocol.lower() == "udp":
            protocol = "17"

        egress = True
        egress = direction != "inbound"
        dryrun = dryrun.lower() != "false"
        try:
            return network_acl.create_entry(
                CidrBlock = cidr_block,
                DryRun = dryrun,
                Egress = egress,
                IcmpTypeCode = {
                    'Code': 123,
                    'Type': 123
                },
                PortRange = {
                    'From': int(portrange_from),
                    'To': int(portrange_to)
                },
                Protocol = protocol,
                RuleAction = rule_action,
                RuleNumber = int(rule_number),
            )
        except botocore.exceptions.ClientError as e:
            print(f"Error: {e}")
            return f"{e}"

    #Terminate, Start and Stop Instance
    def instance_state_change(self, access_key, secret_key, region, instance_id, action, dryrun):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        instance = self.ec2.Instance(instance_id)
        dryrun = dryrun in ["True", "true"]

        try:
            if action == "terminate":
                return instance.terminate(DryRun = dryrun)
            elif action == "start":
                return instance.start(DryRun = dryrun)
            else:
                return instance.stop(DryRun = dryrun)
        except botocore.exceptions.ClientError as e:
            print(f"Error: {e}")
            return f"{e}"
    
    #Create Network Interface
    def create_network_interface(self, access_key, secret_key, region, subnetid, description, dryrun ):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            return client.create_network_interface(
                Description = description,
                DryRun = dryrun,
                SubnetId = subnetid
            )
        except Exception as e:
            return e

    #Create Image
    def create_image(self, access_key, secret_key, region, description, instance_id, name, dryrun, noreboot):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        noreboot = dryrun in {"True", "true"}
        try:
            return client.create_image(
                Description=description,
                DryRun = dryrun,
                InstanceId = instance_id,
                Name = name,
                NoReboot = noreboot
            )   
        except Exception as e:
            return e

    #Deregister Image
    def deregister_an_image(self, access_key, secret_key, region, image_id, dryrun):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            return client.deregister_image(
                ImageId = image_id,
                DryRun = dryrun
            )
        except Exception as e:
            return e
    
    #Create Snapshot
    def create_snapshot(self, access_key, secret_key, region, description, volume_id, dryrun):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            response = client.create_snapshot(
                Description = description,
                VolumeId = volume_id,
                DryRun = dryrun
            )
            return json.dumps(response, default=datetime_handler)
        except Exception as e:
            return e
    
    #Delete Snapshot
    def delete_snapshot(self, access_key, secret_key, region, snapshot_id, dryrun):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            return client.delete_snapshot(
            SnapshotId = snapshot_id,
            DryRun = dryrun
        )
        except Exception as e:
            return e

    #Delete Network Interface
    def delete_network_interface(self, access_key, secret_key, region, networkinterface_id, dryrun):
        self.ec2 = self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            return client.delete_network_interface(
            NetworkInterfaceId = networkinterface_id,
            DryRun=dryrun
        )
        except Exception as e:
            return e

    #Describing address
    def describe_address(self, access_key, secret_key, region, publicips, dryrun):
        self.ec2=self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            lt = [] if len(publicips)==0 else (publicips.split(','), )
            return client.describe_addresses(
                PublicIps = lt,
                DryRun = dryrun
            )
        except Exception as e:
            return e

    #Describing key pair
    def describe_keypair(self, access_key, secret_key, region,  dryrun, option, value):
        self.ec2=self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            lt = [] if len(value)==0 else value.split(',')
            if option == 'KeyNames':
                return client.describe_key_pairs(
                    KeyNames=lt,   
                    DryRun = dryrun
                )
            elif option == 'KeyPairIds':
                return client.describe_key_pairs(
                    KeyPairIds=lt,
                    DryRun = dryrun 
                ) 
            else:
                return client.describe_key_pairs(
                    DryRun = dryrun
                )
        except Exception as e:
            return e

    #Describing network acls
    def describe_networkacls(self, access_key, secret_key, region, dryrun, networkAcl_Id):
        self.ec2=self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:        
            if len(networkAcl_Id) == 0:
                return client.describe_network_acls(
                    DryRun = dryrun,
                )
            lt=networkAcl_Id.split(',')
            return client.describe_network_acls(
                DryRun = dryrun,
                NetworkAclIds = lt
            )
        except Exception as e:
            return e

    #Describing Security groups
    def describe_securitygroups(self, access_key, secret_key, region, dryrun, option, value):
        self.ec2=self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            lt = [] if len(value)==0 else value.split(',')
            if option == 'GroupIds':
                return client.describe_security_groups(
                    GroupIds=lt,   
                    DryRun = dryrun
                )
            # elif option == 'GroupNames':
            #     return client.describe_security_groups(
            #         GroupNames=lt,
            #         DryRun = dryrun 
            #     ) 
            else:
                return client.describe_security_groups(
                    DryRun = dryrun
                )
        except Exception as e:
            return e

    #Describing vpcs
    def describe_vpc(self, access_key, secret_key, region, dryrun, vpcid):
        self.ec2=self.auth_ec2(access_key, secret_key, region)
        client = self.ec2.meta.client
        dryrun = dryrun in ["True", "true"]
        try:
            lt = [] if len(vpcid)==0 else vpcid.split(',')
            return client.describe_vpcs(
                DryRun = dryrun,
                VpcIds = lt
            )
        except Exception as e:
            return e

    def create_an_instance(self, access_key, secret_key, region, dryrun, image_id, min_count, max_count, instance_type, user_data, key_name, security_group_ids):
        client = boto3.resource('ec2', 
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region)
        dryrun = dryrun in ["True", "true"]    

        try:
            if security_group_ids:
                security_group_ids_list = list(security_group_ids.split(" "))
                instance =  client.create_instances(
                                DryRun= dryrun,
                                ImageId=image_id,
                                MinCount=int(min_count),
                                MaxCount=int(max_count),
                                InstanceType=instance_type,
                                KeyName=key_name,
                                SecurityGroupIds= security_group_ids_list,
                                UserData= user_data

                            )
            else:
                instance =  client.create_instances(
                                DryRun= dryrun,
                                ImageId=image_id,
                                MinCount=int(min_count),
                                MaxCount=int(max_count),
                                InstanceType=instance_type,
                                KeyName=key_name,
                                UserData= user_data
                            )
                #parsing response         
            total_instances = [f"instance_id_{str(i)}" for i in range(1,len(instance)+1)]
            instance_id_list = [i.id for i in instance]
            response = dict(zip(total_instances,instance_id_list))
            response["Success"] = "True"
            return response
        except Exception as e:
            return f"Exception occured: {e}"        


if __name__ == "__main__":
    AWSEC2.run()
