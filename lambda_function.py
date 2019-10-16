# AWS EBS Snapshot
# Backup all in-use volumes in all regions

import boto3
import datetime

def lambda_handler(event, context):
    
    ec2 = boto3.client('ec2')
    
    # Get list of regions
    regions = ec2.describe_regions().get('Regions',[] )

    # Iterate over regions
    for region in regions:
        print "Checking region %s " % region['RegionName']
        reg = region['RegionName']

        # Connect to region
        ec2 = boto3.client('ec2', region_name=reg)
    
        # Get all in-use volumes in all regions  
        result = ec2.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}])
        
        # set the current date
        current_date = datetime.datetime.now()
            
        # set snapshots to expire in 30 days
        expiration_date = current_date + datetime.timedelta(30,0) 
        
        for volume in result['Volumes']:
            print "Backing up %s in %s\n" % (volume['VolumeId'], volume['AvailabilityZone'])

            # Create snapshot
            result = ec2.create_snapshot(VolumeId=volume['VolumeId'],Description='Backup created %s GMT' % current_date.strftime("%Y-%m-%d %H:%M:%S"))
        
            # Get snapshot resource 
            ec2resource = boto3.resource('ec2', region_name=reg)
            snapshot = ec2resource.Snapshot(result['SnapshotId'])
        
            volumename = 'N/A'
        
            # Find name tag for volume if it exists
            if 'Tags' in volume:
                for tags in volume['Tags']:
                    if tags["Key"] == 'Name':
                        volumename = tags["Value"]
        
            # Add volume name to snapshot for easier identification
            snapshot.create_tags(Tags=[
                {'Key': 'Name','Value': volumename},
                {'Key': 'Taken Date','Value': '%s' % current_date.strftime("%Y-%m-%d %H:%M:%S")},
                {'Key': 'Expiration Date','Value': '%s' % expiration_date.strftime("%Y-%m-%d %H:%M:%S")},
                {'Key': 'Type','Value': 'Backup'},
                {'Key': 'Requested By','Value': 'Lamba Function > EBS Create Snapshots'}
            ])
            