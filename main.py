import asyncio
import math
import logging
import random
import time
import aiomqtt
import re 
import argparse
from dali.driver.hid import tridonic, hasseb
from dali.gear.general import Up, Down, SetMinLevel, SetMaxLevel, DAPC, RecallMaxLevel, RecallMinLevel, QueryActualLevel, Off
from dali.address import Broadcast

async def connect_dali():

    dali_dev = tridonic("/dev/dali/daliusb-*", glob=True)
    dali_dev.connect()
    print("Waiting to be connected...")
    await dali_dev.connected.wait()
    print(f"Connected, firmware={dali_dev.firmware_version}, serial={dali_dev.serial}")
    return dali_dev

async def connect_mqtt(addr,port=8883,ca_certs=None, username=None, password=None):
    
    tls_params = None
    if ca_certs != "":
        tls_params = aiomqtt.client.TLSParameters(ca_certs=ca_certs)

    client = aiomqtt.Client("mqtt.happyswing.at",port=8883, username=username, password=password, tls_params = tls_params,tls_insecure=True)
    await client.connect()
    print("MQTT client connected.")
    return client

def map_value( value, min=0, max=254): 
    if value < 0 or value > 100: 
        raise ValueError("Value must be between 0 and 100")
    
    return  max * value/100.0 + min * (1.0 - value/100.0)

async def puplish_error_message(client, message: str): 
    await client.publish("error/raspberry", payload=message)

async def handle_dim_value(dali_dev,address, dim_value ):

    if not dim_value.isdigit():
        raise ValueError("Dim payload must be integer!")

    dim_value = int(dim_value)
    dim_value = int(map_value(dim_value, 0,254))
    await dali_dev.send(DAPC(address, dim_value))

def extract_led_id(topic):
    pattern = r"cmd/led/(\d+)/dim"
    match = re.search(pattern, topic)
    if match:
        led_id = int(match.group(1))
        return led_id
    else:
        raise Exception("No integer found in the MQTT topic.") 

async def main(args):
   
    dali_dev = await connect_dali()
    mqtt_client = await connect_mqtt(addr=args.mqtt_address, port=args.mqtt_port,ca_certs=args.ca_certs, username= args.mqtt_username, password=args.mqtt_password)
    
    async with mqtt_client.messages() as msgs:
        await mqtt_client.subscribe("cmd/led/#")
        async for msg in msgs:
            
            try: 
                print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

                if msg.topic.matches("cmd/led/all/dim"): 
                    dim_value = msg.payload.decode()
                    await handle_dim_value(dali_dev,Broadcast(), dim_value)

                elif msg.topic.matches("cmd/led/+/dim"): 
                    dim_value = msg.payload.decode()
                    led_id = extract_led_id(str(msg.topic))
                    await handle_dim_value(dali_dev,led_id, dim_value)

                else:
                    raise Exception("Message with unhandled Topic recieved!")

            except Exception as e: 
                print(f"Exception: {e}")
                await puplish_error_message(mqtt_client, str(e))

    dali_dev.disconnect()
    mqtt_client.close()

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Parse MQTT configuration parameters")
    
    parser.add_argument("--mqtt_address", default="mqtt.happyswing.at", help="MQTT broker address")
    parser.add_argument("--mqtt_port", type=int, default=8333, help="MQTT broker port")
    parser.add_argument("--ca_certs", default="mqtt.happyswing.at_cacert.pem",help="Path to CA certificates")
    parser.add_argument("--mqtt_username", default="happyswing", help="MQTT username")
    parser.add_argument("--mqtt_password", default="mohapmohap!", help="MQTT password")
    
    args = parser.parse_args()

    asyncio.run(main(args))
