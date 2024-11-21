import requests

def is_malicious_url(url):
    # api_key = ''
    api_key = 'hello'
    safe_browsing_url = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
    
    payload = {
        'client': {
            'clientId': "social",
            'clientVersion': "1.0"
        },
        'threatInfo': {
            'threatTypes': ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            'platformTypes': ["ANY_PLATFORM"],
            'threatEntryTypes': ["URL"],
            'threatEntries': [{'url': url}]
        }
    }
    
    response = requests.post(safe_browsing_url, params={'key': api_key}, json=payload)
    data = response.json()

    #  return threats detected
    return 'matches' in data
