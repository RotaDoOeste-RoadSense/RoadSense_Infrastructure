import yaml
import requests
def main(folder, way='N', production=False):
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    response = requests.post(cfg['api_trip_manager']['url'],data={'path': folder, 'way': way,'starting_city': '','ending_city': '', 'production' : production})
    print(response.text)
    return int(response.json()['trip_id'])
# id = main()
if __name__ == '__main__':
    id = main("/mnt/hd1/Extracoes/PGRS_2025")
    print(id)
