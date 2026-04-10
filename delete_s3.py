import boto3

s3 = boto3.client(
    's3',
    endpoint_url='https://s3api-eu-ro-1.runpod.io',
    aws_access_key_id='user_39RRDmK0AEZr14tsLycXnxjLKUz',
    aws_secret_access_key='rps_KO6RIJ4P9N5NRHGQ80GI4FBEWEMTOXMKG7Q3HQK6e2r937',
    region_name='eu-ro-1'
)

def delete_prefix(prefix):
    print(f"Starting deletion for {prefix}...")
    deleted_count = 0
    continuation_token = None
    while True:
        kwargs = {'Bucket': '93jvlq9lix', 'Prefix': prefix, 'MaxKeys': 1000}
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        
        try:
            res = s3.list_objects_v2(**kwargs)
        except Exception as e:
            print(f"Error listing: {e}")
            break
            
        if 'Contents' not in res:
            print(f"No contents found for {prefix}")
            break
            
        objects_to_delete = [{'Key': obj['Key']} for obj in res['Contents']]
        
        if objects_to_delete:
            delete_res = s3.delete_objects(Bucket='93jvlq9lix', Delete={'Objects': objects_to_delete})
            if 'Deleted' in delete_res:
                deleted_count += len(delete_res['Deleted'])
            print(f"Deleted batch. Total deleted so far: {deleted_count} in {prefix}...")
            if 'Errors' in delete_res:
                print(f"Errors deleting: {delete_res['Errors'][:5]}")
            
        if res.get('IsTruncated'):
            next_token = res.get('NextContinuationToken')
            if next_token == continuation_token:
                print("Pagination loop detected! Breaking to avoid infinite loop.")
                # We can't safely paginate further using NextContinuationToken if it's identical
                # However, since we just DELETED the objects, a fresh query WITHOUT a continuation token
                # will give us the NEXT batch of 1000 objects!
                continuation_token = None
                continue
            continuation_token = next_token
        else:
            print(f"Finished deleting {prefix}. Total deleted: {deleted_count}")
            break

delete_prefix('ComfyUI/output/')
delete_prefix('.cache/huggingface/')
