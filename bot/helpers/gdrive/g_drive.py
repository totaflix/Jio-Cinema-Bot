

import os
import pickle
import urllib.parse as urlparse
from urllib.parse import parse_qs

import re
import json
from requests.utils import quote as rquote
import logging
import time

from google.auth.transport.requests import Request # pylint: disable = import-error
from google.oauth2 import service_account # pylint: disable = import-error
from google_auth_oauthlib.flow import InstalledAppFlow # pylint: disable = import-error
from googleapiclient.discovery import build # pylint: disable = import-error
from googleapiclient.errors import HttpError # pylint: disable = import-error
from googleapiclient.http import MediaFileUpload # pylint: disable = import-error
from tenacity import * # pylint: disable = import-error

from pyrogram import Client, enums
from pyrogram.types import Message

from bot import Config
from bot.helpers.progress import Progress
from bot.helpers.gdrive.utils import * # pylint: disable=unused-wildcard-import


LOGGER = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
SERVICE_ACCOUNT_INDEX = 0


class gDrive:
    def __init__(self, bot: Client, message: Message, name=None):
        self.__G_DRIVE_TOKEN_FILE = "token.pickle"
        # Check https://developers.google.com/drive/scopes for all available scopes
        self.__OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
        # Redirect URI for installed apps, can be left as is
        self.__REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
        self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
        self.__G_DRIVE_BASE_DOWNLOAD_URL = "https://drive.google.com/uc?id={}&export=download"
        self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = "https://drive.google.com/drive/folders/{}"
        self.__client = bot
        self.__message = message
        self.__service = self.authorize()
        self._file_uploaded_bytes = 0
        self.uploaded_bytes = 0
        self.UPDATE_INTERVAL = 5
        self.start_time = 0
        self.total_time = 0
        self._should_update = True
        self.is_uploading = True
        self.is_cancelled = False
        self.status = None
        self.updater = None
        self.name = name
        self.update_interval = 3
        self.path = []

    def cancel(self):
        self.is_cancelled = True
        self.is_uploading = False

    def speed(self):
        """
        It calculates the average upload speed and returns it in bytes/seconds unit
        :return: Upload speed in bytes/second
        """
        try:
            return self.uploaded_bytes / self.total_time
        except ZeroDivisionError:
            return 0

    @staticmethod
    def getIdFromUrl(link: str):
        if "folders" in link or "file" in link:
            regex = r"https://drive\.google\.com/(drive)?/?u?/?\d?/?(mobile)?/?(file)?(folders)?/?d?/([-\w]+)[?+]?/?(w+)?"
            res = re.search(regex,link)
            if res is None:
                raise IndexError("GDrive ID not found.")
            return res.group(5)
        parsed = urlparse.urlparse(link)
        return parse_qs(parsed.query)['id'][0]

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    def _on_upload_progress(self):
        if self.status is not None:
            chunk_size = self.status.total_size * self.status.progress() - self._file_uploaded_bytes
            self._file_uploaded_bytes = self.status.total_size * self.status.progress()
            LOGGER.debug(f'Uploading {self.name}, chunk size: {get_readable_file_size(chunk_size)}')
            self.uploaded_bytes += chunk_size
            self.total_time += self.update_interval

    def __upload_empty_file(self, path, file_name, mime_type, parent_id=None):
        media_body = MediaFileUpload(path,
                                     mimetype=mime_type,
                                     resumable=False)
        file_metadata = {
            'name': file_name,
            'description': 'mirror',
            'mimeType': mime_type,
        }
        if parent_id is not None:
            file_metadata['parents'] = [parent_id]
        return self.__service.files().create(supportsTeamDrives=True,
                                             body=file_metadata, media_body=media_body).execute()

    def switchServiceAccount(self):
        global SERVICE_ACCOUNT_INDEX
        service_account_count = len(os.listdir("accounts"))
        if SERVICE_ACCOUNT_INDEX == service_account_count - 1:
            SERVICE_ACCOUNT_INDEX = 0
        SERVICE_ACCOUNT_INDEX += 1
        LOGGER.info(f"Switching to {SERVICE_ACCOUNT_INDEX}.json service account")
        self.__service = self.authorize()

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    def __set_permission(self, drive_id):
        permissions = {
            'role': 'reader',
            'type': 'anyone',
            'value': None,
            'withLink': True
        }
        return self.__service.permissions().create(supportsTeamDrives=True, fileId=drive_id,
                                                   body=permissions).execute()

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    async def upload_file(self, file_path, file_name, mime_type, parent_id):
        # File body description
        file_metadata = {
            'name': file_name,
            'description': 'Transloader',
            'mimeType': mime_type,
        }
        if parent_id is not None:
            file_metadata['parents'] = [parent_id]
        
        if os.path.getsize(file_path) == 0:
            media_body = MediaFileUpload(file_path,
                                         mimetype=mime_type,
                                         resumable=False)
            response = self.__service.files().create(supportsTeamDrives=True,
                                                     body=file_metadata, media_body=media_body).execute()
            if not Config.IS_TEAM_DRIVE:
                self.__set_permission(response['id'])

            drive_file = self.__service.files().get(supportsTeamDrives=True,
                                                    fileId=response['id']).execute()
            download_url = self.__G_DRIVE_BASE_DOWNLOAD_URL.format(drive_file.get('id'))
            meta = self.getFileMetadata(drive_file.get('id'))
            mime_type = meta.get("mimeType")
            if mime_type is None:
                mime_type = 'File'
            msg = f'<b>Name: </b><code>{drive_file.get("name")}</code>'
            msg += f'\n\n<b>Size: </b>{get_readable_file_size(int(meta.get("size", 0)))}'
            msg += f'\n\n<b>Type: </b>{mime_type}'
            index_url = ""
            view_url = ""
            if Config.INDEX_URL is not None:
                url_path = rquote(f'{drive_file.get("name")}', safe='')
                index_url = f'{Config.INDEX_URL}/{url_path}'
                view_url = f'{Config.INDEX_URL}/{url_path}?a=view'
            return msg, download_url, index_url, view_url
        
        media_body = MediaFileUpload(file_path,
                                     mimetype=mime_type,
                                     resumable=True,
                                     chunksize=50 * 1024 * 1024)

        prgs = Progress(None, self.__client, self.__message)
        start_time = time.time()

        # Insert a file
        drive_file = self.__service.files().create(supportsTeamDrives=True,
                                                   body=file_metadata, media_body=media_body)
        response = None
        while response is None:
            if self.is_cancelled:
                return "Upload Cancelled", "https://t.me", "", ""
            try:
                self.status, response = drive_file.next_chunk()
                if self.status and round((time.time() - start_time) % float(5)) == 0:
                    uploaded = self.status.resumable_progress
                    total = self.status.total_size
                    await prgs.progress_for_pyrogram(uploaded, total, "Uploading to Gdrive", start_time)

            except HttpError as err:
                if err.resp.get('content-type', '').startswith('application/json'):
                    reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
                    if reason == 'userRateLimitExceeded' or reason == 'dailyLimitExceeded':
                        if Config.USE_SERVICE_ACCOUNTS:
                            self.switchServiceAccount()
                            LOGGER.info(f"Got: {reason}, Trying Again.")
                            return await self.upload_file(file_path, file_name, mime_type, parent_id)
                    else:
                        raise err
        self._file_uploaded_bytes = 0
        # Insert new permissions
        if not Config.IS_TEAM_DRIVE:
            self.__set_permission(response['id'])
        # Define file instance and get url for download
        drive_file = self.__service.files().get(supportsTeamDrives=True, fileId=response['id']).execute()
        download_url = self.__G_DRIVE_BASE_DOWNLOAD_URL.format(drive_file.get('id'))
        file_id = self.getIdFromUrl(download_url)
        meta = self.getFileMetadata(file_id)
        mime_type = meta.get("mimeType")
        if mime_type is None:
            mime_type = 'File'
        msg = f'<b>Name: </b><code>{drive_file.get("name")}</code>'
        msg += f'\n\n<b>Size: </b>{get_readable_file_size(int(meta.get("size", 0)))}'
        msg += f'\n\n<b>Type: </b>{mime_type}'
        index_url = ""
        view_url = ""
        if Config.INDEX_URL is not None:
            url_path = rquote(f'{drive_file.get("name")}', safe='')
            index_url = f'{Config.INDEX_URL}/{url_path}'
            view_url = f'{Config.INDEX_URL}/{url_path}?a=view'
        return msg, download_url, index_url, view_url

    async def upload(self, file_name: str, path: str):
        
        if Config.USE_SERVICE_ACCOUNTS:
            self.service_account_count = len(os.listdir("accounts"))
        
                
        size = get_readable_file_size(get_path_size(path))
        
        LOGGER.info("Uploading File: " + path)
        
        self.start_time = time.time()
        
        self.updater = setInterval(self.update_interval, self._on_upload_progress)
        
        if os.path.isfile(path):
            try:
                mime_type = get_mime_type(path)
                
                link = await self.upload_file(path, file_name, mime_type, Config.PARENT_ID)
                
                if link is None:
                    raise Exception('Upload has been manually cancelled')
                LOGGER.info("Uploaded To G-Drive: " + path)
                
            except Exception as e:
                
                if isinstance(e, RetryError): # pylint: disable = undefined-variable
                    LOGGER.info(f"Total Attempts: {e.last_attempt.attempt_number}") # pylint: disable = no-member
                    err = e.last_attempt.exception() # pylint: disable = no-member
                else:
                    err = e
                    
                LOGGER.error(err)
                return (f"<b>Error:</b> <code>{err}</code>", "https://t.me", "", "")
            
            finally:
                
                self.updater.cancel()
        else:
            link = ("<b>Error:</b> <code>Only files can be uploaded</code>", "https://t.me", "", "")
                
        LOGGER.info("Deleting downloaded file/folder..")
        return link

    
    
    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    def getFileMetadata(self,file_id):
        return self.__service.files().get(supportsAllDrives=True, fileId=file_id,
                                              fields="name,id,mimeType,size").execute()

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    def getFilesByFolderId(self,folder_id):
        page_token = None
        q = f"'{folder_id}' in parents"
        files = []
        while True:
            response = self.__service.files().list(supportsTeamDrives=True,
                                                   includeTeamDriveItems=True,
                                                   q=q,
                                                   spaces='drive',
                                                   pageSize=200,
                                                   fields='nextPageToken, files(id, name, mimeType,size)',
                                                   pageToken=page_token).execute()
            for file in response.get('files', []):
                files.append(file)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5), # pylint: disable = undefined-variable
           retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG)) # pylint: disable = undefined-variable
    def create_directory(self, directory_name, parent_id):
        file_metadata = {
            "name": directory_name,
            "mimeType": self.__G_DRIVE_DIR_MIME_TYPE
        }
        if parent_id is not None:
            file_metadata["parents"] = [parent_id]
        file = self.__service.files().create(supportsTeamDrives=True, body=file_metadata).execute()
        file_id = file.get("id")
        if not Config.IS_TEAM_DRIVE:
            self.__set_permission(file_id)
        LOGGER.info("Created Google-Drive Folder:\nName: {}\nID: {} ".format(file.get("name"), file_id))
        return file_id

    def authorize(self):
        # Get credentials
        credentials = None
        if not Config.USE_SERVICE_ACCOUNTS:
            if os.path.exists(self.__G_DRIVE_TOKEN_FILE):
                with open(self.__G_DRIVE_TOKEN_FILE, 'rb') as f:
                    credentials = pickle.load(f)
            if credentials is None or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.__OAUTH_SCOPE)
                    LOGGER.info(flow)
                    credentials = flow.run_console(port=0)

                # Save the credentials for the next run
                with open(self.__G_DRIVE_TOKEN_FILE, 'wb') as token:
                    pickle.dump(credentials, token)
        else:
            LOGGER.info(f"Authorizing with {SERVICE_ACCOUNT_INDEX}.json service account")
            credentials = service_account.Credentials.from_service_account_file(
                f'accounts/{SERVICE_ACCOUNT_INDEX}.json',
                scopes=self.__OAUTH_SCOPE)
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def escapes(self, str):
        chars = ['\\', "'", '"', r'\a', r'\b', r'\f', r'\n', r'\r', r'\t']
        for char in chars:
            str = str.replace(char, '\\'+char)
        return str
