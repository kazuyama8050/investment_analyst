import smtplib
from email.mime.text import MIMEText
import traceback

TO_ADDRESS = "kazuki118050@gmail.com"
FROM_ADDRESS = "kazuki118050@gmail.com"
MY_PASSWORD = "bsok wlbz usbr lpse"

def send_mail(msg):
    try:
        smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpobj.ehlo()
        smtpobj.starttls()
        smtpobj.ehlo()
        smtpobj.login(FROM_ADDRESS, MY_PASSWORD)
        smtpobj.sendmail(FROM_ADDRESS, TO_ADDRESS, msg.as_string())
        smtpobj.close()
        return True
    except:
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    msg = MIMEText("テスト本文")
    msg['Subject'] = "テスト"
    msg['From'] = FROM_ADDRESS
    msg['To'] = TO_ADDRESS

    result = send_mail(msg)
    print(result)

