import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import uuid
import streamlit as st
from pathlib import Path
from datetime import datetime
import pytz

class DynamoDBManager:
    def __init__(self):
        # Load secrets from .streamlit/secrets.toml
        self._load_aws_credentials()
        self._initialize_aws_clients()
        self.kst = pytz.timezone('Asia/Seoul')

    def _load_aws_credentials(self):
        """Load AWS credentials from secrets.toml"""
        try:
            self.aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
            self.aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
            self.aws_region_name = st.secrets["AWS_REGION_NAME"]
            self.dynamodb_table_name = st.secrets["DYNAMODB_TABLE_NAME"]
            self.s3_bucket_name = st.secrets["S3_BUCKET_NAME"]
        except Exception as e:
            raise Exception(f"Failed to load AWS credentials: {str(e)}")

    def _initialize_aws_clients(self):
        """Initialize AWS DynamoDB and S3 clients"""
        try:
            self.dynamodb = boto3.resource(
                "dynamodb",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region_name
            )
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region_name
            )
            self.table = self.dynamodb.Table(self.dynamodb_table_name)
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise Exception(f"AWS credentials error: {str(e)}")

    def upload_to_s3(self, content, content_type="text/plain"):
        """Upload content to S3 and return the URL"""
        try:
            file_key = f"contents/{uuid.uuid4()}.txt"
            self.s3.put_object(
                Bucket=self.s3_bucket_name,
                Key=file_key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            return f"s3://{self.s3_bucket_name}/{file_key}"
        except Exception as e:
            raise Exception(f"S3 upload error: {str(e)}")

    def insert_chat_data(self, student_id, timestamp, who, content, context):
        """Insert chat data into DynamoDB with S3 content storage"""
        try:
            # Ensure timestamp is in KST if not already
            if not timestamp.endswith('+09:00'):
                timestamp = datetime.now(self.kst).isoformat()
                
            content_url = self.upload_to_s3(content)
            response = self.table.put_item(
                Item={
                    "student_id": student_id,
                    "timestamp": timestamp,
                    "data": {
                        "who": who,
                        "content": content_url,
                        "context": context
                    }
                }
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to insert chat data: {str(e)}")

    def get_chat_data(self, student_id, timestamp):
        """Retrieve chat data from DynamoDB"""
        try:
            response = self.table.get_item(
                Key={
                    "student_id": student_id,
                    "timestamp": timestamp
                }
            )
            return response.get("Item")
        except Exception as e:
            raise Exception(f"Failed to get chat data: {str(e)}")
