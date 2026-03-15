import boto3
from datetime import datetime, timedelta

def get_lambda_metrics(function_name, access_key, secret_key, region, hours=1):
    """Fetches real-time invocation counts from CloudWatch."""
    try:
        cw_client = boto3.client(
            'cloudwatch',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        response = cw_client.get_metric_data(
            MetricDataQueries=[{
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Lambda',
                        'MetricName': 'Invocations',
                        'Dimensions': [{'Name': 'FunctionName', 'Value': function_name.split(':')[0]}]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'ReturnData': True,
            }],
            StartTime=start_time,
            EndTime=end_time,
            ScanBy='TimestampAscending'
        )

        results = response['MetricDataResults'][0]
        return results['Timestamps'], results['Values']
    except Exception as e:
        print(f"CloudWatch Error: {e}")
        return [], []