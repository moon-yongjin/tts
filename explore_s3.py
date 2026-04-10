import boto3
import json

s3 = boto3.client(
    's3',
    endpoint_url='https://s3api-eu-ro-1.runpod.io',
    aws_access_key_id='user_39RRDmK0AEZr14tsLycXnxjLKUz',
    aws_secret_access_key='rps_KO6RIJ4P9N5NRHGQ80GI4FBEWEMTOXMKG7Q3HQK6e2r937',
    region_name='eu-ro-1'
)

res = s3.list_objects_v2(Bucket='93jvlq9lix', Prefix='ComfyUI/', Delimiter='/')
print("Subfolders in ComfyUI/:")
for cp in res.get('CommonPrefixes', []):
    print("  " + cp['Prefix'])

res2 = s3.list_objects_v2(Bucket='93jvlq9lix', Prefix='output/', Delimiter='/')
print("\nItems in root output/:")
for obj in res2.get('Contents', [])[:10]:
    print("  " + obj['Key'] + f" ({obj['Size']} bytes)")
for cp in res2.get('CommonPrefixes', []):
    print("  " + cp['Prefix'])
