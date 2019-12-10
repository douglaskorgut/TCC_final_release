# -*- coding: utf-8 -*-
from __future__ import print_function
import time
import paho.mqtt.client as mqtt


class MqttRouter:
    def __init__(self, client_id):
        self.restart_system = False
        self.record_video = False
        self.release_video = False
        self.publish_image = False
        self.unrecognize = False
        self.recognize = False

        # MQTT sub topics
        self.PUBLISH_IMAGE_TOPIC = 'horus/image/publish'
        self.RESTART_SYSTEM_TOPIC = 'horus/system/restart'
        self.SYSTEM_UNRECOGNIZE = 'horus/system/unrecognize'
        self.RECORD_VIDEO_TOPIC = 'horus/video/record'
        self.RELEASE_VIDEO_TOPIC = 'horus/video/release'
        self.SYSTEM_RECOGNIZE = 'horus/system/recognize'

        self.client_id = client_id
        self._mqttc = None

    def mqtt_on_connect(self, mqttc, obj, flags, rc):
        if rc is 0:
            print("Connected!")
            self._mqttc.subscribe(self.PUBLISH_IMAGE_TOPIC, 0)
            self._mqttc.subscribe(self.RESTART_SYSTEM_TOPIC, 0)
            self._mqttc.subscribe(self.RECORD_VIDEO_TOPIC, 0)
            self._mqttc.subscribe(self.RELEASE_VIDEO_TOPIC, 0)
            self._mqttc.subscribe(self.SYSTEM_UNRECOGNIZE, 0)
            self._mqttc.subscribe(self.SYSTEM_RECOGNIZE, 0)

    def mqtt_on_message(self, mqttc, obj, msg):
        message_rec = msg.payload.decode("utf-8")

        if msg.topic == self.RESTART_SYSTEM_TOPIC:
            if str(message_rec) == "true":
                self.restart_system = True

        if msg.topic == self.PUBLISH_IMAGE_TOPIC:
            if str(message_rec) == "true":
                self.publish_image = True

        if msg.topic == self.RECORD_VIDEO_TOPIC:
            print("Recording video")
            if str(message_rec) == "true":
                self.record_video = True

        if msg.topic == self.RELEASE_VIDEO_TOPIC:
            print("Releasing video")
            if str(message_rec) == "true":
                self.release_video = True

        if msg.topic == self.SYSTEM_UNRECOGNIZE:
            if str(message_rec) == "true":
                self.unrecognize = True

        if msg.topic == self.SYSTEM_RECOGNIZE:
            if str(message_rec) == "true":
                self.recognize = True

    def on_disconnect(self, client, userdata, rc):
        self._mqttc.unsubscribe(self.PUBLISH_IMAGE_TOPIC)
        self._mqttc.unsubscribe(self.RELEASE_VIDEO_TOPIC)
        self._mqttc.unsubscribe(self.RECORD_VIDEO_TOPIC)
        self._mqttc.unsubscribe(self.RESTART_SYSTEM_TOPIC)
        self._mqttc.unsubscribe(self.SYSTEM_UNRECOGNIZE)
        self._mqttc.unsubscribe(self.SYSTEM_UNRECOGNIZE)

    def mqtt_on_publish(self, mqttc, obj, mid):
        print("mid: " + str(mid))

    def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def publish(self, topic, message):
        if self._mqttc:
            try:
                self._mqttc.publish(topic, message)
            except UnicodeDecodeError:
                pass

    def initialize(self):
        try:
            self._mqttc = mqtt.Client(transport='websockets')
            self._mqttc.ws_set_options('/ws')
            self._mqttc.on_message = self.mqtt_on_message
            self._mqttc.on_connect = self.mqtt_on_connect
            self._mqttc.on_subscribe = self.mqtt_on_subscribe
            self._mqttc.on_publish = self.mqtt_on_publish
            self._mqttc.on_disconnect = self.on_disconnect
            print("MqttRouter initialized!")

        except Exception as e:
            print('Initialization error')
            print(e)
            return

    def run(self):
        try:
            self._mqttc.connect("test.mosquitto.org", 8080, 20)
        except Exception as e:
            print('Error occured connecting do mosquitto broker')
            print(e)

        try:
            self._mqttc.loop_start()
        except Exception as e:
            print(e)
            time.sleep(10)


if __name__ == '__main__':

    mqttc = MqttRouter('horus_client')
    try:
        mqttc.initialize()
        mqttc.run()
        print('sup')
    except Exception as e:
        print(e)



