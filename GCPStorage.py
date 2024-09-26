
import os
import json
import logging
from dotenv import load_dotenv
from google.cloud.storage import Client
from google.oauth2 import service_account

class GCPStorage(object):
    '''Google CLoud Platform Storage IO 
    
    https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python

    https://cloud.google.com/python/docs/reference/storage/1.44.0/client

    https://googleapis.dev/python/google-auth/1.7.0/user-guide.html

    '''
    _is_ready = False

    def __new__(cls):
        """ creates a singleton object, if it is not created, 
        or else returns the previous singleton object"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(GCPStorage, cls).__new__(cls)
        return cls.instance

    def setup(self, env_file):
        if self._is_ready:
            return

        load_dotenv(env_file)
        self._auth_json = os.environ.get('JSON_AUTH_PATH')
        self._storage_scopes = [os.environ.get('GCP_STORAGE_SCOPES')]
        self._credentials = service_account.Credentials.from_service_account_file(
            self._auth_json,
            scopes=self._storage_scopes)

        self._storage_client = Client(credentials=self._credentials)
        self._is_ready = True

    def upload_file(self, source_file_name, destination_bucket, destination_blob_name):
        """Uploads a file to the bucket."""
        if not self._is_ready:
            return

        # The ID of your GCS bucket
        # bucket_name = "your-bucket-name"
        # The path to your file to upload
        # source_file_name = "local/path/to/file"
        # The ID of your GCS object
        # destination_blob_name = "storage-object-name"

        bucket = self._storage_client.bucket(destination_bucket)
        blob = bucket.blob(destination_blob_name)

        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request to upload is aborted if the object's
        # generation number does not match your precondition. For a destination
        # object that does not yet exist, set the if_generation_match precondition to 0.
        # If the destination object already exists in your bucket, set instead a
        # generation-match precondition using its generation number.
        generation_match_precondition = None # 0

        blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

        logging.warning(f"File {source_file_name} uploaded to {destination_blob_name}.")

    def upload(self, files, destination_bucket, destination_folder: str = None):
        """Upload one or more files to the cloud blob storage"""
        if not self._is_ready:
            return

        if isinstance(files, str):
            try:
                f_basename = os.path.basename(files)
                if destination_folder is None:
                    self.upload_file(files, destination_bucket, f_basename)
                else:
                    self.upload_file(files, destination_bucket, os.path.join(destination_folder,f_basename))
            except Exception as e:
                logging.warning(e)

        if isinstance(files, list):
            for f in files:
                try:
                    f_basename = os.path.basename(f)
                    if destination_folder is None:
                        self.upload_file(files, destination_bucket, f_basename)
                    else:
                        self.upload_file(files, destination_bucket, os.path.join(destination_folder,f_basename))
                except Exception as e:
                    logging.warning(e)
                    
    def download_file(self, destination_filename, source_bucket, source_blob_name):
        bucket = self._storage_client.get_bucket(source_bucket)
        blob = bucket.blob(source_blob_name)
        file_data = blob.download_as_string().decode()

        with open(destination_filename, 'w') as fout:
            fout.write(file_data)
            
    def download(self, destination_folder, source_bucket, source_blob_names):
        """Upload one or more files to the cloud blob storage"""
        if not self._is_ready:
            return

        if isinstance(source_blob_names, str):
            f = source_blob_names
            try:
                if destination_folder is None:
                    self.download_file(f, source_bucket, f)
                else:
                    self.download_file(os.path.join(destination_folder, f), source_bucket, f)
            except Exception as e:
                logging.warning(e)

        if isinstance(source_blob_names, list):
            for f in source_blob_names:
                try:
                    if destination_folder is None:
                        self.download_file(f, source_bucket, f)
                    else:
                        self.download_file(os.path.join(destination_folder, f), source_bucket, f)
                except Exception as e:
                    logging.warning(e)
    
    def list_blobs(self, bucket_name):
        """Lists all the blobs in the bucket."""
        # bucket_name = "your-bucket-name"

        # Note: Client.list_blobs requires at least package version 1.17.0.
        blobs = self._storage_client.list_blobs(bucket_name)
        
        files = []
        # Note: The call returns a response only when the iterator is consumed.
        for blob in blobs:
            files.append(blob.name)
            
        return files
        
    def create_file(self, file_name, destination_bucket, destination_folder: str = None):
        with open(file_name, 'w') as f:
            f.write('')
        
        self.upload(file_name, destination_bucket, destination_folder)

        try:
            os.remove(file_name)
        except OSError:
            pass
        