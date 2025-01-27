## OCI-ClaimIP
Manage floating IP addresses between OCI Instances using an IP address assigned as secondary IP Address.

# Requirements:
- this script needs to run inside the instance wanting to make the claim
- python needs to be installed and the python OCI module needs to be available
- The instance needs to have the permissions to remove and assign the IP address via Dynamic Group membership

# Usage:
python claimip.py ip-address-you-want-to-claim

