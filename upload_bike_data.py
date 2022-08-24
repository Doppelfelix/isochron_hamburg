#%%
from io import StringIO
from itertools import chain
import json
from multiprocessing import Pool
import json
import logging
from urllib.request import urlopen


import boto3
from tqdm.contrib.concurrent import process_map

bucket = "biking-data"
csv_buffer = StringIO()


base_bike_url = "https://iot.hamburg.de/v1.1/Things?$skip=0&$top=5000&$filter=((properties%2FownerThing+eq+%27DB+Connect%27))"


def get_stations():
    response = json.loads(urlopen(base_bike_url).read())
    return response["value"]


def get_station_urls(station):
    try:
        thingID = station["@iot.id"]
        datastream_url = station["Datastreams@iot.navigationLink"]
        description = station["description"]
    except ValueError:
        logging.error("Not valid value found.")

    return {
        "thingID": thingID,
        "datastream_url": datastream_url,
        "description": description,
    }


def get_obs_stream(station):
    try:
        response = json.loads(urlopen(station["datastream_url"]).read())["value"]
        keep_datastream = response[0]
        obs_stream = keep_datastream["Observations@iot.navigationLink"]

        coordinatesAll = keep_datastream["observedArea"]["coordinates"]

        coordinatesX = "NA"
        coordinatesY = "NA"

        def get_correct_vals(item):
            if any(isinstance(subitem, list) for subitem in item):

                for subitem in item:
                    if any(isinstance(subsubitem, list) for subsubitem in subitem):
                        return get_correct_vals(subitem)

                    if len(subitem) == 2:
                        if (
                            subitem[0] > 0
                            and subitem[0] <= 180
                            and subitem[1] > 0
                            and subitem[1] <= 180
                        ):
                            return subitem[0], subitem[1]

            else:
                return item[0], item[1]

        coordinatesX, coordinatesY = get_correct_vals(coordinatesAll)

        return {
            "thingID": station["thingID"],
            "description": station["description"],
            "obs_stream": obs_stream,
            "coordinatesX": coordinatesX,
            "coordinatesY": coordinatesY,
        }

    except KeyError:
        logging.error(
            f"No proper observation stream for ID {station['thingID']} found."
        )


def get_obs(station):

    obs_url = (
        station["obs_stream"]
        + "?$top=5000&$skip={}&$filter=date(phenomenontime)+gt+date('2010-01-01')"
    )
    list_of_obs = []
    for i in range(0, 10000000, 5000):
        obs_iter = json.loads(urlopen(obs_url.format(i)).read())["value"]
        if len(obs_iter) == 0:
            break
        list_of_obs = list_of_obs + obs_iter

    return list_of_obs


def clean_obs(obs):
    observationID = obs["@iot.id"]
    resultTime = obs["resultTime"]
    result = obs["result"]

    return {
        "result": result,
        "resultTime": resultTime,
        "observationID": observationID,
    }


def export_to_s3(name, file):
    s3_resource = boto3.resource("s3")
    s3_resource.Object(bucket, name).put(
        Body=(bytes(json.dumps(file, indent=4).encode("UTF-8")))
    )


def export_obs_for_station(station):
    list_of_cleaned_obs = []
    station_stream = get_station_urls(station)
    obs_stream = get_obs_stream(station_stream)
    all_obs = get_obs(obs_stream)
    for obs in all_obs:
        clean_ob = clean_obs(obs)
        list_of_cleaned_obs.append(clean_ob)

    meta_dict = {
        key: obs_stream[key]
        for key in ("thingID", "description", "coordinatesX", "coordinatesY")
    }
    meta_dict["obs"] = list_of_cleaned_obs

    filename = f"bike_station_{station['@iot.id']}.json"

    export_to_s3(filename, meta_dict)


def run():
    all_stations = get_stations()
    with Pool() as p:
        res = process_map(export_obs_for_station, all_stations)


if __name__ == "__main__":
    run()
