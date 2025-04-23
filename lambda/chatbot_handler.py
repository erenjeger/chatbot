import json
import boto3
import os
import uuid
import datetime
import requests

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        query = body.get("query", "").lower()

        if "weather" in query:
            city = query.split("in")[-1].strip()
            response_text = get_weather(city)
        elif "joke" in query:
            response_text = get_joke()
        else:
            response_text = "Sorry, I can only tell weather and jokes."

        log_to_dynamodb(query, response_text)

        return {
            'statusCode': 200,
            'body': json.dumps({"response": response_text}),
            'headers': {'Content-Type': 'application/json'}
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    res = requests.get(url)
    if res.status_code != 200:
        return "I couldn't find the weather for that city."
    data = res.json()
    temp = data['main']['temp']
    desc = data['weather'][0]['description']
    return f"The weather in {city.title()} is {desc} with {temp}°C."

def get_joke():
    res = requests.get("https://official-joke-api.appspot.com/jokes/random")
    if res.status_code != 200:
        return "Sorry, I couldn't fetch a joke."
    joke = res.json()
    return f"{joke['setup']} - {joke['punchline']}"

def log_to_dynamodb(query, response):
    table.put_item(
        Item={
            'query_id': str(uuid.uuid4()),
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'query': query,
            'response': response
        }
    )
