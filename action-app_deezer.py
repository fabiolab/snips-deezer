#!/usr/bin/env python3

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes

# imported to get type check and IDE completion
from hermes_python.ontology.dialogue.intent import IntentMessage
import requests
from urllib.parse import urljoin
from loguru import logger

CONFIG_INI = "config.ini"

# if this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
#
# hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

DEEZER_BASE_URL = "https://api.deezer.com"
DEEZER_SEARCH_ENDPOINT = "/search"


class DeezerApp(object):
    """class used to wrap action code with mqtt connection
       please change the name refering to your application
    """

    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except Exception:
            self.config = None

        # start listening to MQTT
        self.start_blocking()

    @staticmethod
    def play_track(hermes: Hermes, intent_message: IntentMessage):

        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        logger.info("[Received] intent: {}".format(intent_message.intent.intent_name))
        logger.info("[Received] slots: {} / {}".format(intent_message.slots.keys(), intent_message.slots.values()))

        searched_track = intent_message.slots.get("musicTrack", "obladi oblada")

        track_id = DeezerApp.get_deezer_id(searched_track)

        # if need to speak the execution result by tts
        hermes.publish_start_session_notification(
            intent_message.site_id, str(track_id), ""
        )

    def master_intent_callback(self, hermes, intent_message):
        logger.info("[Received] intent {}".format(intent_message.intent.intent_name))
        coming_intent = intent_message.intent.intent_name
        if coming_intent == "fabio35:playSong":
            self.play_track(hermes, intent_message)

        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

    @staticmethod
    def get_deezer_id(searched_track) -> str:
        url = urljoin(DEEZER_BASE_URL, DEEZER_SEARCH_ENDPOINT)

        try:
            parameters = {"q": searched_track}
            logger.info("Calling {} for getting track id {}".format(url, searched_track))
            response = requests.get(url, params=parameters)
            if response.status_code >= 400:
                e = Exception(
                    "HTTP Error calling {} => {} : {}".format(
                        url, response.status_code, response.text
                    )
                )
                logger.info(e)
                return "je n'ai pas trouvé de chanson portant ce titre"
            response_json = response.json()
            return DeezerApp.parse_response(response_json)
        except Exception as e:
            logger.info(e)
            return "je n'ai pas trouvé de chanson portant ce titre"

    @staticmethod
    def parse_response(response: dict) -> str:
        logger.info("Parsing response ...")
        if not response or not response.get("data", None):
            return "je n'ai pas trouvé de chanson portant ce titre"

        try:
            results = response["data"][0].get("id", "pas d'identifiant")
        except Exception as e:
            return "arg"
        return results


if __name__ == "__main__":
    DeezerApp()
