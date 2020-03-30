import sys
import socket
import base64
import random
import string
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
from threading import Thread
import getpass
class CryptoClient():
	def __init__(self):
		print "Welcome to CryptoChat, a secure P2P chat client"

		self.IP = raw_input("Please enter the IP address you wish to chat with: ")
		self.PORT = int(raw_input("Enter the port for communication: "))
		print
		print "Now enter the keys for the different encryption methods, make sure they are different."
		print "Please note they will not be printed for your security."
		print
		self.EncryptKeyXOR = getpass.getpass("Enter desired key for XOR encryption: ")
		self.EncryptKeyAES = hashlib.md5(getpass.getpass("Enter a secure passphrase for AES: ")).hexdigest()
		###AES padding
		BS = 16
		self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
		self.unpad = lambda s : s[:-ord(s[len(s)-1:])]
		###Start chat server and client
		Thread(target=self.RecvMSG, args=()).start()
		self.SendMSG()
	def EncryptAES(self,raw):
		raw = self.pad(raw)
		iv = Random.new().read( AES.block_size )
		cipher = AES.new( self.EncryptKeyAES, AES.MODE_CBC, iv )
		return base64.b64encode( iv + cipher.encrypt( raw ) )
	def DecryptAES(self,enc):
		enc = base64.b64decode(enc)
		iv = enc[:16]
		cipher = AES.new(self.EncryptKeyAES, AES.MODE_CBC, iv )
		return self.unpad(cipher.decrypt( enc[16:] ))
	def XOR(self,securekey,data,mode):
		if mode == 1:
			securekey=securekey[::-1]
		temp=''
		for char in securekey:
			for x in data:
				temp += chr(ord(x)^ord(char))
			data=temp
			temp=''
		return data	
	def EncryptMSG(self,data):
		data = self.XOR(self.EncryptKeyXOR,data,0)
		data = self.EncryptAES(data)
		return data
	def DecryptMSG(self,data):
		data = self.DecryptAES(data)
		data = self.XOR(self.EncryptKeyXOR,data,1)
		return data
	def SendMSG(self):
		clientsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		print
		print "You are now talking to '"+self.IP+"'"
		while 1:
			message = raw_input("")
			if message.startswith("/send"): #send file command
				self.SendFILE(message.split(" ")[1])
				continue
			if message=="/leave":
				message = self.EncryptMSG("\x03")
				clientsock.sendto(message, (self.IP, self.PORT))
				sys.exit(0)
			if message.startswith("/msg"):
				self.IP=message.split(" ")[1]
				print "[CLIENT] You are now talking to '"+self.IP+"'"
				continue
			else:
				message = self.EncryptMSG("\x01"+message)
				clientsock.sendto(message, (self.IP, self.PORT))
	def SendFILE(self,file_):
		if file_.startswith(".") or file_.startswith("/"): #added security measure.
			print "[CLIENT] For security and safety reasons, filenames starting with '.' or '/' will not be sent. Aborting."
		else:
			clientsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
			data="\x02"+file_+"\xFF"
			f=open(file_,"rb")
			data+=f.read()
			f.close()
			data = self.EncryptMSG(data)
			clientsock.sendto(data, (self.IP, self.PORT))
			print "[CLIENT] File Sent!"
	def RandStr(self,length):
		return ''.join(random.choice(string.letters) for _ in range(length))
	def RecvMSG(self):
		serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
		serversocket.bind((self.IP, self.PORT))
		while 1:
			(data, addr) = serversocket.recvfrom(1073741824) # buffer size is 1 gbit (for large files/images)
			data = self.DecryptMSG(data)
			if data.startswith("\x02"):
				filename=''
				data=list(data)
				del data[0]
				for i in data:
					if i=="\xFF":
						break
					else:
						filename += i
				del data[0] # delete protocol char
				del data[:len(filename)] # delete file end char
				if filename.startswith(".") or filename.startswith("/"): #attempted exploit!
					print "[!!!ALERT!!!] "+addr[0] + " has attempted to overwrite your " + filename
				else:
					print "[CLIENT] " + addr[0] + " has sent " + filename
					print "[CLIENT] Downloading..."
					data=''.join(data)
					f = open(filename,"wb")
					f.write(data)
					f.close()
					print "[CLIENT] Saved."
			elif data.startswith("\x01"): # all messages start with "\x01" to prevent file spamming
				data=list(data)
				del data[0]
				data=''.join(data)
				print "["+addr[0]+"] >	|	"+data
			elif data.startswith("\x03"):
				print "[CLIENT] "+addr[0]+" has left."
				sys.exit(0)

if __name__=="__main__":
	CryptoClient()

