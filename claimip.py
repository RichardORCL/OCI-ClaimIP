# ClaimIP: Script to claim an IP address as secondary IP address in OCI
# This script can be used to claim an "floating" IP address between instances
#
# Requirements:
# - this script needs to run inside the instance wanting to make the claim
# - python needs to be installed and the python OCI module needs to be available
# - The instance needs to have the permissions to remove and assign the IP address via Dynamic Group membership
#
# Usage:
# python claimip.py ip-address-you-want-to-claim
#
# Written by: richard.garsthage@oracle.com


import oci
import requests
import sys

if len(sys.argv) > 1:
    claimIP = sys.argv[1]
else:
    print("Error: No IP address provided.")
    sys.exit(-1)

# Get OCI authentication via Instance Principle (Dynamic group)
try:
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    config = {'region': signer.region, 'tenancy': signer.tenancy_id}
except Exception:
    print("Error obtaining instance principals certificate, aborting")
    sys.exit(-1)

# Create Network and Compute API clients based on Instance Principle authentication
virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)
compute_client = oci.core.ComputeClient(config, signer=signer)

def get_instance_metadata():
    metadata_url = "http://169.254.169.254/opc/v2/instance/"
    headers = {"Authorization": "Bearer Oracle"}
    response = requests.get(metadata_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_vnics_from_instance(instance_ocid, compartment_id):
    vnics = []
    try:
        vnic_attachments = compute_client.list_vnic_attachments(compartment_id=compartment_id, instance_id=instance_ocid).data
        for vnic_attachment in vnic_attachments:
            vnic = virtual_network_client.get_vnic(vnic_attachment.vnic_id).data
            vnics.append(vnic)
    except oci.exceptions.ServiceError as e:
        print(f"Error retrieving VNICs: {e}")
    return vnics


def claim_ip_as_secondary(ip_address, vnic_id):

    # see if IP is already used, and if so, remove from current assigned vnic
    vnic = virtual_network_client.get_vnic(vnic_id).data
    subnet_id = vnic.subnet_id

    # Get all private IPs in the subnet
    private_ips = virtual_network_client.list_private_ips(subnet_id=subnet_id).data

    if ip_address:
        for private_ip in private_ips:
            if private_ip.ip_address == ip_address:
                # Remove the IP from the VNIC that is using it
                virtual_network_client.delete_private_ip(private_ip.id)

    # Assign the IP as a secondary private IP to the new vnic
    create_private_ip_details = oci.core.models.CreatePrivateIpDetails(
        ip_address=ip_address,
        vnic_id=vnic_id
    )
    virtual_network_client.create_private_ip(create_private_ip_details)

meta = get_instance_metadata()  # Retrieve instance meta data from OCI control plane
vnics = get_vnics_from_instance(instance_ocid=meta['id'], compartment_id=meta['compartmentId'])  # Get the VNICs attached to this Instance
claim_ip_as_secondary(ip_address=claimIP, vnic_id=vnics[0].id) # Claim the provided IP addess to the first attached VNIC

print ("{} has been claimed".format(claimIP))
