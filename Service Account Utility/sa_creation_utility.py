import json
from google.auth.transport.requests import Request
import urllib.parse
import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from sa_help import ServAcc,AddEmailsToGroup



SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/iam','https://www.googleapis.com/auth/admin.directory.group','https://www.googleapis.com/auth/admin.directory.group.member']

def authorise(creds=None):
    if os.path.exists('creds.pickle'):
        with open('creds.pickle', 'rb') as handle:
            creds = pickle.load(handle)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        credentials = {
                        "installed": {
                                "client_id": G_DRIVE_CLIENT_ID,
                                "client_secret": G_DRIVE_CLIENT_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": [
                                    "http://localhost"
                                ]
                            }
                    }
        flow = InstalledAppFlow.from_client_config(credentials,SCOPES)

        flow.redirect_uri = 'http://localhost:1'
        auth_url, _ = flow.authorization_url(access_type='offline')
        print(f"Visit the following URL and the authorise. You will be redirected to a **error page**. That page's url would be something like:\nhttps://localhost:1/XXXXXXXXX\n\nCopy that url and send here\n\n{auth_url}")
        redir_url = input('enter the url: ')
        query = urllib.parse.urlparse(redir_url).query
        code = urllib.parse.parse_qs(query)['code'][0]
        # code = redir_url
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open('creds.pickle', 'wb') as handle:
            pickle.dump(creds, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return creds
    else:
        return creds
    

# sas_cls = ServAcc(authorise())

def listprojects(sas_cls):
    desc = ''
    for idx,i in enumerate(sas_cls._list_projects()):
        desc+=f"{idx+1}. {i}\n"
    print(desc)


def createsa(sas_cls,projectid):
    sas_cls.enableservices(projectid)
    sas_cls.createsas(projectid)
    print('Successfully Created Service accounts, use downloadsazip` to get the service accounts in json format.\nUse `saemails` to get the emails of the service accounts.')

def downloadsa(sas_cls,projectid):
    if not os.path.exists('accounts') or len(os.listdir('accounts')) == 0:
        sas_cls.download_keys(projectid)
        # print('downloaded !!!')
    else:
        raise Exception('An accounts folder already exists in this directory! Remove that first then continue')

def saemails():
    list_of_acc_fname = os.listdir('accounts')
    if os.path.exists('emails.txt'):
        os.remove('emails.txt')
    with open('emails.txt','a') as f:
        for i in list_of_acc_fname:
            with open(f'accounts/{i}') as f2:
                data = json.load(f2)
            f.write(data["client_email"]+"\n")

guide_url = "https://rentry.co/sacreationutility"

print("Welcome to service account creation utility\n")
print('Made by yours truly, jsmsj#5252')
print()
print(f"Step one is to get the credentials.json file.\nFollow the guide at ({guide_url}) to do so.")
print('Checking if credentials.json file exists......')
if not os.path.exists('credentials.json') and not os.path.exists('creds.pickle'):
    print(f'Credentials.json file does not exist. Please follow the guide at ({guide_url}) to do so.')
print('Congrats, credentials.json file exists.')
with open('credentials.json','r') as f:
    data = json.load(f)
    G_DRIVE_CLIENT_ID = data['installed']['client_id']
    G_DRIVE_CLIENT_SECRET = data['installed']['client_secret']

credentials = authorise()
sas_cls = ServAcc(credentials)
print('\nChoose the project in which you want to create your service accounts\n')
projs = sas_cls._list_projects()
for idx,val in enumerate(projs):
    print(f'{idx+1}. {val}')

proj_id = projs[int(input('\nWhich project do you want to choose.... (eg: 2): '))-1]

print('\nEnabling Services Please wait....')
sas_cls.enableservices(proj_id)
print('\nSuccessfully Enabled Services.')
print(f'\nNow creating 100 SERVICE ACCOUNTS in {proj_id}')

sas_cls.createsas(proj_id)

print('\nDownloading service accounts now..')
downloadsa(sas_cls,proj_id)
print('\nDownloaded Service accounts !\nYou can find them in the accounts folder.')
print('\nRenaming those service accounts')
base = "accounts"
count = 0
for file in os.listdir(base):
    abspath = os.path.join(base,file)
    destpath = os.path.join(base,f"{count}.json")
    os.rename(abspath,destpath)
    count += 1
print('\nCreating an emails.txt file')
saemails()
print('\nemails.txt file has been created.')

print('My work here is done!\nYou should add emails from emails.txt into a google group, 10 emails at a time.\nThen add the group to a shared drive of your choice.\nEnjoy!')
# add2group = AddEmailsToGroup(credentials)

# add2group.add_emails_to_group(input('\nEnter the google group email, where service accounts should be added: '))
# print('My work here is done!\nYou should add the group to a shared drive of your choice.\nEnjoy!')
