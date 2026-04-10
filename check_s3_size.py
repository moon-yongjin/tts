import boto3
from collections import defaultdict

s3 = boto3.client(
    's3',
    endpoint_url='https://s3api-eu-ro-1.runpod.io',
    aws_access_key_id='user_39RRDmK0AEZr14tsLycXnxjLKUz',
    aws_secret_access_key='rps_KO6RIJ4P9N5NRHGQ80GI4FBEWEMTOXMKG7Q3HQK6e2r937',
    region_name='eu-ro-1'
)

bucket_name = '93jvlq9lix'
folder_sizes = defaultdict(int)
total_size = 0

try:
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            size = obj['Size']
            total_size += size
            # Get the top-level folder
            parts = obj['Key'].split('/')
            if len(parts) > 1:
                top_folder = parts[0]
                folder_sizes[top_folder] += size
            else:
                folder_sizes['/'] += size

    print(f"Total Bucket Size: {total_size / (1024**3):.2f} GB")
    print("\nTop level folder sizes:")
    for folder, size in sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {folder}/: {size / (1024**3):.2f} GB")

except Exception as e:
    print(f"Error: {e}")
