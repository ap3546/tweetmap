from flask import Flask, request, render_template
import json
import os.path
from datetime import datetime
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

# Note that Amazon EB looks for application.py (not run.py, start.py, etc.)

# Amazon Elastic Beanstalk looks for 'application' object
application = Flask(__name__)

# case of keywords doesn't matter because checked using .lower() -> not case sensitive
kws = ["Trump", "ethereum", "bitcoin", "factom", "litecoin", "monero", "ripple", "zcash", "golem", "the"]

host = 'search-twittmap-gcds3wfs2vumozclk6my2anjda.us-east-1.es.amazonaws.com'
ind = 'twitter'
mapping_type = 'tweet'
AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
AWS_SECRET_KEY = "AWS_SECRET_KEY"
REGION = "us-east-1"

awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

file_path = os.path.dirname(__file__)

def convert(original_time):
    timestamp = datetime.strptime(original_time, '%m-%d-%Y %I:%M %p')
    return timestamp.strftime('%a %b %d %H:%M:%S +0000 %Y')

@application.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@application.route('/global', methods=['POST'])
def get_global():
    '''View function for sending tweet points

    Args:
        None

    Returns:
        Dumped json file containing desired twitter points.
    '''
    keyword = request.args['kw'].lower()
    start = convert(request.args['start'])
    end = convert(request.args['end'])
    payload = {
        "size": 1000,
        'query': {
            'bool': {
                'must': {
                    'match': {
                        'keyword': keyword
                    }
                },
                'filter': {
                    'range': {
                        'timestamp': {"gte": start, "lte": end}
                    }
                }
            }
        },
        "sort": [
            {"timestamp": "asc"}
        ]
    }
    search_res = es.search(index=ind, doc_type=mapping_type, body=payload)
    response = {'tweets': [], 'count': 0, 'pattern': 'global'}
    for hit in search_res['hits']['hits']:
        response['tweets'].append(hit['_source']['coordinates'])
        response['count'] += 1
    return json.dumps(response, indent=3)

@application.route('/local', methods=['POST'])
def get_local():
    keyword = request.args['kw'].lower()
    start = convert(request.args['start'])
    end = convert(request.args['end'])
    lat = request.args['lat']
    lon = request.args['lon']
    distance = '300km'

    # large max size since already restricting to 300km radius
    payload = {
        "size": 10000,
        'query': {
            'bool': {
                'must': {
                    'match': {
                        'keyword': keyword
                    }
                },
                'filter': {
                    'range': {
                        'timestamp': {"gte": start, "lte": end}
                    }
                },
                'filter': {
                    'geo_distance': {
                        'distance': distance,
                        'coordinates': {
                            'lat': lat,
                            'lon': lon
                        }
                    }
                }
            }
        },
        "sort": [
            {"timestamp": "asc"}
        ]
    }

    search_res = es.search(index=ind, doc_type=mapping_type, body=payload)
    response = {'tweets': [], 'count': 0, 'pattern': 'local'}
    for hit in search_res['hits']['hits']:
        response['tweets'].append("@" + hit['_source']['author'] + " (" + hit['_source']['timestamp'] + ")" + ": " + hit['_source']['text'])
        response['count'] += 1
    return json.dumps(response, indent=3)

if __name__=='__main__':
    # for testing
    #application.run(debug=True)
    # when deployed, Amazon EB by default forwards requests to port 5000
    application.run(host='0.0.0.0', port=5000)
