# -*- coding: utf-8 -*-

'''
发送邮件：
    收取邮件使用IMAP协议，起用ssl，端口993
    发送邮件使用SMTP协议，起用ssl，端口465

参数：
    user：发送者，格式为string
    password：发送者密码，格式string
    receivers：接收邮件的人，格式list
    subject：邮件主题，格式string
    mail_server_smtp：smtp邮件服务器地址
    timeout：超时时间
    attachment：邮件附件文件绝对路径，格式string
'''

from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


class SendMail(object):
    def __init__(self, user, password, receivers, subject, mail_server_smtp, timeout=30):
        '''接收邮件变量'''
        self.user = user
        self.password = password
        self.receivers = receivers
        self.subject = subject
        self.mail_server_smtp = mail_server_smtp
        self.timeout = timeout

    def sendmail(self, content=None, attachment=None, attachment_name=None):
        '''发送邮件，如果需要发送附件，则修改attachment为附件绝对路径'''
        # 设置邮件标题、发送者和接收者
        msg = MIMEMultipart()
        msg['Subject'] = self.subject
        msg['From'] = self.user
        msg['To'] = ','.join(self.receivers)

        # 设置邮件正文
        part = MIMEText(content, "plain", "utf-8")
        msg.attach(part)

        # 如果有附件则添加附件
        if attachment is not None:
            part = MIMEApplication(open(attachment, 'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename=attachment_name)
            msg.attach(part)

        # 发送邮件
        send = SMTP_SSL(self.mail_server_smtp, timeout=self.timeout)
        send.login(self.user, self.password)
        send.sendmail(self.user, self.receivers, msg.as_string())
        send.close()
