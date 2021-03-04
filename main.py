# -*- coding: UTF-8 -*-

import requests as req
import json
import time 
from nacl import encoding, public
from base64 import b64encode
import os


gh_token=os.getenv('GH_TOKEN')
gh_repo=os.getenv('GH_REPO')
ms_token=os.getenv('MS_TOKEN')
client_id=os.getenv('CLIENT_ID')
client_secret=os.getenv('CLIENT_SECRET')

Auth=r'token '+gh_token

if gh_repo == '':
    gh_repo = 'kylinpoet/office_e5_api'    

puturl=r'https://api.github.com/repos/'+gh_repo+r'/actions/secrets/MS_TOKEN'
geturl=r'https://api.github.com/repos/'+gh_repo+r'/actions/secrets/public-key'
key_id='kylinpoet'


def getpublickey(Auth,geturl):
    headers={'Accept': 'application/vnd.github.v3+json','Authorization': Auth}
    html = req.get(geturl,headers=headers)
    jsontxt = json.loads(html.text)
    public_key = jsontxt['key']
    global key_id 
    key_id = jsontxt['key_id']
    return public_key



def createsecret(public_key,secret_value):
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")



def setsecret(encrypted_value,key_id,puturl):
    headers={
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': Auth
            }
    data={
         'encrypted_value': encrypted_value,
         'key_id': key_id
         }
    for retry_ in range(4):
        putstatus=req.put(puturl,headers=headers,data=json.dumps(data))
        if putstatus.status_code < 300:
            print(r'微软密钥上传成功')
            break
        else:
            if retry_ == 3:
                print(r'微软密钥上传失败')        
    return putstatus

def getmstoken(ms_token):
    headers={
            'Content-Type':'application/x-www-form-urlencoded'
            }
    data={
         'grant_type': 'refresh_token',
         'refresh_token': ms_token,
         'client_id':client_id,
         'client_secret':client_secret,
         # 'redirect_uri':r'https://login.microsoftonline.com/common/oauth2/nativeclient',
         'redirect_uri':r'http://localhost:53682/'
         }
    for retry_ in range(4):
        html = req.post('https://login.microsoftonline.com/common/oauth2/v2.0/token',data=data,headers=headers)
        if html.status_code < 300:
            print(r'微软密钥获取成功')
            break
        else:
            if retry_ == 3:
                print(r'微软密钥获取失败')
                print(html.json())  
    return html.json()['access_token']


mstoken = getmstoken(ms_token)

def sendEmail(content):
    headers={
            'Authorization': 'bearer ' + mstoken,
            'Content-Type': 'application/json'
            }
    mailmessage={
                'message':{
                          'subject': 'Broadcasting',
                          'body': {'contentType': 'HTML', 'content': content},
                          'toRecipients': [{'emailAddress': {'address': 'kylinpoet@163.com'}}],
                          },
                'saveToSentItems': 'true',
                }
    for retry_ in range(4):  
        posttext=req.post(r'https://graph.microsoft.com/v1.0/me/sendMail',headers=headers,data=json.dumps(mailmessage))
        if posttext.status_code < 300:
            print('邮件发送成功')
            break
        else:
            if retry_ == 3:
                print('邮件发送失败')
    print('')


def searchEmail():
    headers={
            'Authorization': 'bearer ' + mstoken,
            'Content-Type': 'application/json'
            }
    for retry_ in range(4): 
        posttext=req.get(r'https://graph.microsoft.com/v1.0/me/messages?$search="hello world"',headers=headers,)
        if posttext.status_code < 300:
            value = posttext.json()['value']
            if len(value)>0:
                print(f"来自 {value[0]['from']['emailAddress']['address']} 的消息：{value[0]['subject']}")
            else:
                print('邮件查询成功')
            break
        else:
            if retry_ == 3:
                print('邮件查询失败')
    print('')

def searchOneDrive():
    headers={
            'Authorization': 'bearer ' + mstoken,
            'Content-Type': 'application/json'
            }
    for retry_ in range(4): 
        posttext=req.get("https://graph.microsoft.com/v1.0/me/drive/root/search(q='qrcode')?select=name,id,webUrl",headers=headers,)
        if posttext.status_code < 300:
            value = posttext.json()['value']
            if len(value)>0:
                print(f"文件 {value[0]['name']} 访问地址为：{value[0]['webUrl']}")
            else:
                print('文件查询成功')
            break
        else:
            if retry_ == 3:
                print('文件查询失败')
    print('')

searchEmail()
time.sleep(3)
searchOneDrive()
encrypted_value=createsecret(getpublickey(Auth,geturl),mstoken)
setsecret(encrypted_value,key_id,puturl)
