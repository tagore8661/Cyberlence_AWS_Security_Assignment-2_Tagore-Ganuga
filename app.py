from flask import Flask, jsonify
import boto3
import json
from botocore.exceptions import ClientError

app = Flask(__name__)

def get_account_public_access_block(s3_control_client, account_id):
    try:
        response = s3_control_client.get_public_access_block(AccountId=account_id)
        config = response['PublicAccessBlockConfiguration']
        return {
            'BlockPublicAcls': config.get('BlockPublicAcls', False),
            'IgnorePublicAcls': config.get('IgnorePublicAcls', False),
            'BlockPublicPolicy': config.get('BlockPublicPolicy', False),
            'RestrictPublicBuckets': config.get('RestrictPublicBuckets', False)
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            return {
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        raise

def get_bucket_public_access_block(s3_client, bucket_name):
    try:
        response = s3_client.get_public_access_block(Bucket=bucket_name)
        config = response['PublicAccessBlockConfiguration']
        return {
            'BlockPublicAcls': config.get('BlockPublicAcls', False),
            'IgnorePublicAcls': config.get('IgnorePublicAcls', False),
            'BlockPublicPolicy': config.get('BlockPublicPolicy', False),
            'RestrictPublicBuckets': config.get('RestrictPublicBuckets', False)
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            return {
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        return {
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        }

@app.route('/discover', methods=['GET'])
def discover_s3_settings():
    try:
        s3_client = boto3.client('s3')
        sts_client = boto3.client('sts')

        account_id = sts_client.get_caller_identity()['Account']
        s3_control_client = boto3.client('s3control')

        account_settings = get_account_public_access_block(s3_control_client, account_id)

        all_settings_true = all([
            account_settings['BlockPublicAcls'],
            account_settings['IgnorePublicAcls'],
            account_settings['BlockPublicPolicy'],
            account_settings['RestrictPublicBuckets']
        ])
        account_status = 'ON' if all_settings_true else 'OFF'

        buckets_response = s3_client.list_buckets()
        buckets = []

        for bucket in buckets_response['Buckets']:
            bucket_name = bucket['Name']
            bucket_settings = get_bucket_public_access_block(s3_client, bucket_name)

            bucket_all_settings_true = all([
                bucket_settings['BlockPublicAcls'],
                bucket_settings['IgnorePublicAcls'],
                bucket_settings['BlockPublicPolicy'],
                bucket_settings['RestrictPublicBuckets']
            ])

            buckets.append({
                'Name': bucket_name,
                'CreationDate': bucket['CreationDate'].isoformat(),
                'PublicAccessBlockConfiguration': bucket_settings,
                'Status': 'ON' if bucket_all_settings_true else 'OFF'
            })

        result = {
            'AccountId': account_id,
            'AccountPublicAccessBlockConfiguration': account_settings,
            'AccountStatus': account_status,
            'Buckets': buckets
        }

        with open('s3_settings.json', 'w') as f:
            json.dump(result, f, indent=2)

        return jsonify({
            'message': 'S3 settings discovered and saved to s3_settings.json',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
