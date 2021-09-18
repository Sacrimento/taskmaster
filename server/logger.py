import logging
import smtplib
from email.message import EmailMessage

class TaskmasterLogger(logging.basicConfig):
    def __init__(self, *args, **kwargs):
        self.mail_addr = kwargs.pop('mail_addr')
        if mail_addr:
            self.mail = smtplib.SMTP('localhost')

        super().__init__(args, kwargs)

    def __del__(self):
        if hasattr(self, 'mail'):
            self.mail.quit()
        super().__del__()

    def _get_mail(self, sub, content):
        if not self.mail_addr:
            return
        
        mail = EmailMessage()
        mail.set_content(content)

        mail['Subject'] = sub
        mail['To'] = self.mail_addr
        mail['From'] = "Taskmaster@42.fr"

        return mail

    def mail(self, level, content):
        mail = self.get_mail('[TASKMASTER] %s', content)
        self.mail.send_message(mail)
