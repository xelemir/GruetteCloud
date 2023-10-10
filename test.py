import requests

ip = '83.135.160.86'
response = requests.get(f'http://ip-api.com/json/{ip}')
data = response.json()

print(f'City: {data["city"]}')
print(f'Region: {data["regionName"]}')
print(f'Country: {data["country"]}')
