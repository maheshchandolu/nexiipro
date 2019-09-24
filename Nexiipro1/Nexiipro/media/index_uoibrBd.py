import smtplib
#import threading 

#k = ["tirupathirao2525@gmail.com", "ravi@gmail.com"]
#for i in range(len(k)):
	#t = smtplib.SMTP('smtp.gmail.com', 587)
	#t.starttls()
	#t.login("tirupathirao2525@gmail.com", "9866495506")
	#message = "Message_you_need_to_send"
	#t.sendmail("sender_email_id", k[i], message)
	#t.quit() 


def email_sending():
	k=["mahesh.chandolu@nexiilabs.com"]
	for i in range(len(k)):
		t=smtplib.SMTP('smtp.gmail.com',587)
		t.ehlo()
		t.starttls()
		t.login("unifiedsimplified.automation@gmail.com","nexiilabs")
		message="message_you_need_send"
		t.sendmail("unifiedsimplified.automation@gmail.com",k[i],message)
		print("_______gone___________")
		t.quit()


email_sending()
