import os
import pickle
from typing import Callable
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from core.domain.pipeline import Step

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_YOUTUBE_SECRETS")

class UploadYoutubeVideoStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        self.upload_video(
            file_path=input.get("file_path", "output.mp4"),
            title=input["title"],
            description=input["description"],
            category_id=input.get("category_id", "22"),
            privacy_status=input.get("privacy_status", "unlisted"),
        )

    def get_authenticated_service(self):
        credentials = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES
                )
                credentials = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(credentials, token)
        return build("youtube", "v3", credentials=credentials)

    def upload_video(self, file_path, title, description, category_id="22", privacy_status="private"):
        youtube = self.get_authenticated_service()
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status
            },
        }
        mediaFile = MediaFileUpload(
            file_path, chunksize=-1, resumable=True, mimetype="video/*"
        )
        request = youtube.videos().insert(
            part="snippet,status", body=request_body, media_body=mediaFile
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload {int(status.progress() * 100)}% complete.")
        print(f"Upload Complete! Video ID: {response['id']}")
        return response["id"]
