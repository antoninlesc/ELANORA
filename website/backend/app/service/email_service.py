"""Service for sending password verification emails."""

import datetime
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from passlib.context import CryptContext
from pydantic import SecretStr

from app.core import config

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Email template paths
TEMPLATES_DIR = Path(__file__).parent.parent / "template" / "emails"
PASSWORD_VERIFICATION_TEMPLATE_EN = TEMPLATES_DIR / "password_verification_en.html"
PASSWORD_VERIFICATION_TEMPLATE_FR = TEMPLATES_DIR / "password_verification_fr.html"


class EmailService:
    """Service for sending password verification and reset emails."""

    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=config.MAIL_USERNAME,
            MAIL_PASSWORD=SecretStr(config.MAIL_PASSWORD),
            MAIL_FROM=config.MAIL_FROM,
            MAIL_PORT=config.MAIL_PORT,
            MAIL_SERVER=config.MAIL_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
        )

    @staticmethod
    def load_template(template_path: Path) -> str:
        """Load an email template from a file."""
        try:
            with open(template_path, encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(
                f"Email template not found: {template_path}"
            ) from err

    async def send_password_reset_verification_email(
        self, email: str, username: str, code: str, language: str = "en"
    ) -> bool:
        """Send a password reset verification email.

        Args:
            email (str): The email address to send the verification code to
            username (str): The username to personalize the email
            code (str): The verification code
            language (str): The language for the email template ("en" or "fr")

        Returns:
            bool: True if the email was sent successfully, False otherwise

        """
        current_year = datetime.datetime.now().year
        contact_url = f"{config.FRONTEND_HOST}/contact"

        # Determine email template and subject based on language
        if language.lower() == "fr":
            subject = "ELANORA - Vérification de votre mot de passe"
            template_path = PASSWORD_VERIFICATION_TEMPLATE_FR
        else:
            subject = "ELANORA - Password Verification"
            template_path = PASSWORD_VERIFICATION_TEMPLATE_EN

        # Load and format the email template
        try:
            template = self.load_template(template_path)
            email_body = template.format(
                username=username,
                code=code,
                year=current_year,
                contact_url=contact_url,
            )
        except Exception as e:
            print(f"[EmailService] Failed to load or format template: {e}")
            # Fallback template in case of error
            if language.lower() == "en":
                email_body = f"""
                <html>
                  <body>
                    <h1>Password Verification</h1>
                    <p>Hello {username},</p>
                    <p>Your verification code is: {code}</p>
                    <p><a href=\"{contact_url}\">Click here to contact support</a></p>
                  </body>
                </html>
                """
            else:
                email_body = f"""
                <html>
                  <body>
                    <h1>Vérification de votre mot de passe</h1>
                    <p>Bonjour {username},</p>
                    <p>Votre code de vérification est : {code}</p>
                    <p><a href=\"{contact_url}\">Cliquez ici pour contacter le support</a></p>
                  </body>
                </html>
                """

        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=email_body,
            subtype=MessageType.html,
        )

        try:
            fm = FastMail(self.conf)
            await fm.send_message(message)
            return True
        except Exception as e:
            print(
                f"[EmailService] Failed to send password reset verification email: {e}"
            )
            raise e
