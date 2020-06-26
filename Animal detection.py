import cv2
import numpy
import datetime
import json
import requests
from watson_developer_cloud import VisualRecognitionV3
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from playsound import playsound
from ibm_botocore.client import Config, ClientError

from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey


authenticator = IAMAuthenticator('VLUrjONwYX2SASsZqZ4UYvnlLYO_NUDZpuoB7BBKefzD')
text_to_speech = TextToSpeechV1(
    authenticator=authenticator
)

text_to_speech.set_service_url('https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/instances/a611c15c-b7b8-4347-b53a-e120c33a518a')

with open('animal.mp3', 'wb') as audio_file:
    audio_file.write(text_to_speech.synthesize('Animal Detected',voice='en-US_AllisonV3Voice',accept='audio/mp3').get_result().content)

import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Constants for IBM COS values
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "AgVMeIzLtiZ9HHQrEjeuGn3dk3xCO44HuzFa2zk1kbPB" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/a0aa3a47516c48b392c9e359c18bd39e:fded7f14-c045-4e63-8bbe-3d7bba66da6e::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"
COS_AUTH_ENDPOINT="https://iam.cloud.ibm.com/identity/token"

# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)
client = Cloudant("4a0a764e-ddd6-40d7-920f-38ebee39c517-bluemix", "0e751379fcea0587f148169b99e14b8a5a4fad921883185b16df76e753d00dc7", url="https://4a0a764e-ddd6-40d7-920f-38ebee39c517-bluemix:0e751379fcea0587f148169b99e14b8a5a4fad921883185b16df76e753d00dc7@4a0a764e-ddd6-40d7-920f-38ebee39c517-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()

database_name = "project"

my_database = client.create_database(database_name)

if my_database.exists():
   print(f"'{database_name}' successfully created.")

def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))

        
cap=cv2.VideoCapture(0)
print(cap.isOpened())

if(cap.isOpened()==False):
    print("Camera cannot be opened")

while(cap.isOpened()):
    ret,frame=cap.read()
    
    cv2.imshow('Video',frame)
    k=cv2.waitKey(100)
    picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    print(picname)
    cv2.imwrite(picname+".jpg",frame)
    visual_recognition = VisualRecognitionV3(
    '2018-03-19',
    iam_apikey='oSxup0fc7B6Y8Cvt_jzTUZ9e9w-NJQti_WjXRZk6A3o2')

    with open(picname+".jpg", 'rb') as images_file:
        classes = visual_recognition.classify(
        images_file,
        threshold='0.6',
	classifier_ids='DefaultCustomModel_872739987').get_result()
        print(classes['images'][0]['classifiers'][0]['classes'])
        for i in (classes['images'][0]['classifiers'][0]['classes']):
            if(i['class']=='forest animal'):
                
                playsound("animal.mp3")
        
                multi_part_upload("neeraja",picname+".jpg" , picname+'.jpg')
                json_document={"link": COS_ENDPOINT+"/"+"neeraja"+"/"+picname+".jpg"}
                new_document = my_database.create_document(json_document)
                if new_document.exists():
                    print(f"Document '{json_document}' successfully created.")
                x=requests.get("https://www.fast2sms.com/dev/bulk?authorization=AFfgEkvJLxUHceChaq5pNQs4jKnG1Zl26VOu0YoSdiBy83X7tbfAgIvlrVmeK0Tt7UoPQHhD24Cqw8LE&sender_id=FSTSMS&message=Animal Detected&language=english&route=p&numbers=7702583858")
                print(x.text)

    if k==ord('q'):
        cap.release()
        cv2.destroyAllWindows()



