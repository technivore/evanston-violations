import boto3
from boto3.dynamodb.conditions import Key, Attr
from chalice import Chalice

TABLE_NAME = 'ev-violations'
BUSINESS_TABLE_NAME = 'ev-businesses'
REGION = 'us-east-1'
MIN_BUSINESS_NAME_LEN = 3
SCAN_SEGMENTS = 2

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
business_table = dynamodb.Table(BUSINESS_TABLE_NAME)
app = Chalice(app_name='chalice-app')
app.debug = True

@app.route('/')
def index():
    # get most recent violations (by violation ID, descending). Only include violations with valid business info. 
    try:
        limit = int(app.current_request.query_params.get('limit'))
    except:
        limit = 20

    resp = table.query(
        IndexName='idx_violation_id',
        KeyConditionExpression=Key('type').eq('violation'),
        FilterExpression=Attr('name').exists(),
        Limit=limit,
        ScanIndexForward=False,
    )
    return resp['Items']

@app.route('/businesses/{business_id}')
def business_violations(business_id):
    # get all violations for selected business, most recent first
    resp = table.query(
        KeyConditionExpression=Key('business_id').eq(business_id),
        ScanIndexForward=False,
    )
    return resp['Items']

@app.route('/search')
def search():
    try:
        s = app.current_request.query_params.get('s').lower().strip()
    except:
        return {}

    if len(s) >= MIN_BUSINESS_NAME_LEN:

        items = {}

        for i in range(SCAN_SEGMENTS):
            resp = business_table.scan(
                FilterExpression=Attr('name_normalized').contains(s),
                ProjectionExpression='business_id, #n',
                ExpressionAttributeNames={'#n': 'name'},
                TotalSegments=SCAN_SEGMENTS,
                Segment=i,
            )

            for i in resp['Items']:
                items[i['name']] = i['business_id']

        return items

    return {}
