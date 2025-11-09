from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from app.core.conf import MAIL_EMAIL, MAIL_HOST, MAIL_PASS, MAIL_PORT
from app.core.logger import setup_logger

logger = setup_logger("services.email")


class EmailService:
    def __init__(self):
        self.conn = ConnectionConfig(
            MAIL_USERNAME=MAIL_EMAIL,
            MAIL_PASSWORD=MAIL_PASS,
            MAIL_FROM=MAIL_EMAIL,
            MAIL_PORT=MAIL_PORT,
            MAIL_SERVER=MAIL_HOST,
            USE_CREDENTIALS=True,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
        )

        self.fm = FastMail(self.conn)

    async def send_mail(self, subject: str, email: EmailStr, body: str, html=True):
        try:
            email = MessageSchema(
                subject=subject,
                recipients=[email],
                body=body,
                subtype="html" if html else "plain",
            )
            print(email)

            await self.fm.send_message(email)
            logger.info(f"Email send to {email}")
        except Exception as e:
            logger.warning(f"Email configuration failed for {email} | error={e}")
