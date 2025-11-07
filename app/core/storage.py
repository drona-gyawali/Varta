import boto3
from botocore.exceptions import ClientError

from app.core.conf import (
    STORJ_ACCESS_KEY_ID,
    STORJ_BUCKET_NAME,
    STORJ_ENDPOINT,
    STORJ_SECRET_ACCESS_KEY,
)
from app.core.logger import setup_logger
from app.utils.utils import construct_url

logger = setup_logger("core.storage")


class Bucket:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=STORJ_ENDPOINT,
            aws_access_key_id=STORJ_ACCESS_KEY_ID,
            aws_secret_access_key=STORJ_SECRET_ACCESS_KEY,
        )
        self.bucket_name = STORJ_BUCKET_NAME

    def create_presigned_url(self, user_id: str, filename: str) -> str:
        if not user_id:
            logger.error("Error | fx=create_presigned_url | error=user not verified")
            raise ValueError("User not authorized")

        key = f"{user_id}-{filename}"
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                },
                ExpiresIn=3600,
                HttpMethod="PUT",
            )

            objects_url = construct_url(key, self.bucket_name)

            return {
                presigned_url,
                objects_url,
            }
        except ClientError as e:
            logger.error(f"ClientError in create_presigned_url: {e}")
            raise e

    def delete_object(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.error(f"ClientError in delete_object: {e}")
            raise e


bucket = Bucket()
