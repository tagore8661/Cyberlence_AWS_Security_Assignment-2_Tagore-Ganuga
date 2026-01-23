# S3 Bucket Settings Discovery API

Flask API to discover S3 bucket settings and analyze public access configurations.

## Setup

1. Configure AWS credentials:
```bash
aws configure
```
Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

```bash
python app.py
```

The API will run on `http://localhost:5000`

## API Endpoints

### 1. Discover S3 Settings
```bash
curl http://localhost:5000/discover
```

This endpoint will:
- Fetch account-level public access block settings
- List all S3 buckets
- Fetch public access block settings for each bucket
- Determine account and bucket status (ON/OFF)
- Save results to `s3_settings.json`

### 2. Health Check
```bash
curl http://localhost:5000/health
```

## Output JSON Structure

```json
{
  "AccountId": "123456789012",
  "AccountPublicAccessBlockConfiguration": {
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  },
  "AccountStatus": "ON",
  "Buckets": [
    {
      "Name": "my-bucket",
      "CreationDate": "2024-01-01T00:00:00",
      "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": false,
        "IgnorePublicAcls": false,
        "BlockPublicPolicy": false,
        "RestrictPublicBuckets": false
      },
      "Status": "OFF"
    }
  ]
}
```

## JQ Commands

### 1. Check Account Status (All Settings True = ON, Otherwise = OFF)

```bash
jq '{AccountStatus: .AccountStatus, AccountPublicAccessBlock: .AccountPublicAccessBlockConfiguration}' s3_settings.json
```
This shows the account status that's already calculated in the JSON. 
(or)
```
curl http://localhost:5000/discover \
| jq '.data | {AccountStatus, AccountPublicAccessBlockConfiguration}'
```

### 2. List All Failing Buckets (Buckets with Public Access when Status is OFF)

```bash
jq '.Buckets[] | select(.Status == "OFF") | .Name' s3_settings.json
```
If account status is ON and all buckets are properly configured, this returns empty.
If status is OFF, it lists all bucket names with public access.

(or)
```
curl http://localhost:5000/discover \
| jq 'if .data.AccountStatus == "ON" then [] else [.data.Buckets[] | select(.Status == "OFF") | .Name] end'

```

### 3. Detailed View of Failing Buckets

```bash
jq '.Buckets[] | select(.Status == "OFF") | {Name, PublicAccessBlockConfiguration}' s3_settings.json
```

### 4. Count of Failing Buckets

```bash
jq '[.Buckets[] | select(.Status == "OFF")] | length' s3_settings.json
```

### 5. Summary Report

```bash
jq '{
  AccountStatus: .AccountStatus,
  TotalBuckets: (.Buckets | length),
  FailingBuckets: [.Buckets[] | select(.Status == "OFF") | .Name]
}' s3_settings.json
```