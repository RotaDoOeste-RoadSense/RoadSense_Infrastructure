import yaml
import requests
def main(folder):
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    response = requests.get(cfg['api_get_cur_trip']['url'],data={'path': folder})
    return int(response.json()['trip_id'])
# id = main()
