import boto3

s3 = boto3.client(
    's3',
    endpoint_url='https://s3api-eu-ro-1.runpod.io',
    aws_access_key_id='user_39RRDmK0AEZr14tsLycXnxjLKUz',
    aws_secret_access_key='rps_KO6RIJ4P9N5NRHGQ80GI4FBEWEMTOXMKG7Q3HQK6e2r937',
    region_name='eu-ro-1'
)

def get_prefix_size(prefix):
    total_size = 0
    continuation_token = None
    while True:
        kwargs = {'Bucket': '93jvlq9lix', 'Prefix': prefix, 'MaxKeys': 1000}
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        try:
            res = s3.list_objects_v2(**kwargs)
        except Exception as e:
            print(f"Error {prefix}: {e}")
            break
            
        for obj in res.get('Contents', []):
            total_size += obj['Size']
            
        if res.get('IsTruncated'):
            next_token = res.get('NextContinuationToken')
            if next_token == continuation_token:
                break
            continuation_token = next_token
        else:
            break
    print(f"Size of {prefix}: {total_size / (1024**3):.2f} GB")

prefixes_to_check = [
    'ComfyUI/models/checkpoints/',
    'ComfyUI/models/unet/',
    'ComfyUI/models/clip/',
    'ComfyUI/models/loras/',
    'lora_training/',
    'ai-toolkit/',
    'ComfyUI/temp/',
    'huggingface/'
]

for p in prefixes_to_check:
    get_prefix_size(p)
