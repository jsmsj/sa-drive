import time
from base64 import b64decode
from random import choice
import os
import traceback
from googleapiclient.discovery import build
import json


SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/iam']

def _generate_id(prefix='saf-'):
    chars = '-abcdefghijklmnopqrstuvwxyz1234567890'
    return prefix + ''.join(choice(chars) for _ in range(25)) + choice(chars[1:])


def _list_sas(iam,project):
    resp = iam.projects().serviceAccounts().list(name='projects/' + project,pageSize=100).execute()
    if 'accounts' in resp:
        return resp['accounts']
    return []

class ServAcc:
    def __init__(self,creds):
        self.scopes = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/iam','https://www.googleapis.com/auth/service.management'] #,'https://www.googleapis.com/auth/admin.directory.group'
        self.sleep_time = 30
        self.creds = creds
        self._services = self.authorise()
        self.services=['iam','drive','serviceusage','cloudresourcemanager']
        self.current_key_dump = []
    
    def authorise(self):
        self.cloud = build('cloudresourcemanager', 'v1', credentials=self.creds)
        self.iam = build('iam', 'v1', credentials=self.creds)
        self.serviceusage = build('serviceusage','v1',credentials=self.creds)
        # self.admin_directory = build('admin', 'directory_v1', credentials=self.creds)
        return [self.cloud,self.iam,self.serviceusage] #,self.admin_directory

    def _list_projects(self) -> list:
        return [i['projectId'] for i in self.cloud.projects().list().execute()['projects']]

    def enableservices(self,projectid) -> None:
        services_links = [i + '.googleapis.com' for i in self.services]
        projects = [projectid]
        batch = self.serviceusage.new_batch_http_request(callback=self._def_batch_resp)
        for i in projects:
            for j in services_links:
                batch.add(self.serviceusage.services().enable(name='projects/%s/services/%s' % (i,j)))
        batch.execute()
    
    def createsas(self,projectid):
        sa_count = len(_list_sas(self.iam,projectid))
        while sa_count != 100:
            self._create_accounts(self.iam,projectid,100 - sa_count)
            sa_count = len(_list_sas(self.iam,projectid))

    def _create_accounts(self,service,project,count):
        batch = service.new_batch_http_request(callback=self._def_batch_resp)
        for i in range(count):
            aid = _generate_id('mfc-')
            batch.add(service.projects().serviceAccounts().create(name='projects/' + project, body={ 'accountId': aid, 'serviceAccount': { 'displayName': aid }}))
        batch.execute()

    def _def_batch_resp(self,id,resp,exception):
        if exception is not None:
            if str(exception).startswith('<HttpError 429'):
                time.sleep(self.sleep_time/100)
            else:
                print(str(exception))

    def download_keys(self,projectid):
        self._create_sa_keys(self.iam,[projectid],'accounts')
        

    def _create_sa_keys(self,iam,projects,path):
        all_projs = self._list_projects()
        all_good = False
        for proj_id in projects:
            if proj_id not in all_projs:
                raise Exception(f"Error: Project id {proj_id} not found, All projects = {all_projs}")
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            for i in projects:
                self.current_key_dump = []
                while self.current_key_dump is None or len(self.current_key_dump) != 100:
                    batch = iam.new_batch_http_request(callback=self._batch_keys_resp)
                    total_sas = _list_sas(iam,i)
                    for j in total_sas:
                        batch.add(iam.projects().serviceAccounts().keys().create(
                            name='projects/%s/serviceAccounts/%s' % (i,j['uniqueId']),
                            body={
                                'privateKeyType':'TYPE_GOOGLE_CREDENTIALS_FILE',
                                'keyAlgorithm':'KEY_ALG_RSA_2048'
                            }
                        ))
                    print("DOWNLOADING SERVICE ACCOUNTS !!!!!!")
                    
                    
                    batch.execute()
                    print("DOWNLOADED SERVICE ACCOUNTS !!!!!!")
                    
                    if self.current_key_dump is None:
                        self.current_key_dump = []
                    else:
                        for j in self.current_key_dump:
                            with open('%s/%s.json' % (path,j[0]),'w+') as f:
                                f.write(j[1])
        except Exception as e:
            print(e)
            traceback.print_exc()

    def _batch_keys_resp(self,id,resp,exception):
        if exception is not None:
            self.current_key_dump = None
            time.sleep(self.sleep_time/100)
        elif self.current_key_dump is None:
            time.sleep(self.sleep_time/100)
        else:
            self.current_key_dump.append((
                resp['name'][resp['name'].rfind('/'):],
                b64decode(resp['privateKeyData']).decode('utf-8')
            ))


class AddEmailsToGroup:
    def __init__(self,creds):
        self.scopes = ['https://www.googleapis.com/auth/admin.directory.group','https://www.googleapis.com/auth/admin.directory.group.member']
        self.creds = creds
        self.service = self.authorise()
        self.cwd = os.getcwd()

    def authorise(self):
        self.service = build("admin", "directory_v1", credentials=self.creds)
        return self.service
    
    def add_emails_to_group(self,group_email):
        batch = self.service.new_batch_http_request()
        sa_files = os.listdir(self.cwd+'\\accounts')
        print('\nProcessing SA files')
        for sa in sa_files:
            ce = json.loads(open(self.cwd + f'\\accounts\\{sa}', 'r').read())['client_email']
            body = {"email": ce, "role": "MEMBER"}
            batch.add(self.service.members().insert(groupKey=group_email, body=body))
        print(f'\nAdding emails to group: {group_email}')
        batch.execute()
        print('\nDone')

