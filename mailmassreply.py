import logging
import datetime
import dateutil.parser
import hashlib
import copy
import re
import os
import imaplib
import smtplib, ssl
import email
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



module_logger = logging.getLogger(__name__)

class MailMassReply(object):
    headerTemplate="""
        <hr/>
        <strong>From:</strong> {from}<br/>
        <strong>Date:</strong> {date}<br/>
        <strong>To:</strong> {to}<br/>
        <strong>Subject:</strong> {subject}<br/>
        <br/>
        <br/>
    """
        
    def __init__(
            self,                        
            config=None,

            # Reply sender address and Reply-To
            sender=None,
            replyto=None,

            # Text for reply
            replytxt='reply.txt',
            replyhtml='reply.html',
        
            # List of addresses to skip and not reply to
            ignore_list=[],
        
            # List of dicts with keys(from, date, to, replyto, subject) to skip replying
            skip_list=[],


            # IMAP server and credentials to read list of e-mails that will get a reply
            imap_server=None,
            imap_folder=None,
            imap_user=None,
            imap_password=None,


            # SMTP server and credentials to use to send replys
            smtp_server=None,
            smtp_user=None,
            smtp_password=None,

            # IMAP filters
            imap_sent_since=datetime.date(1970,1,1),
            imap_sent_before=None,
        
            # If dryrun=True, do everything except sending the e-mail
            dryrun=False,
        
            # For test purposes, send messages to target_impersonation_email address instead of actual teargets
            target_impersonation_email=None
    ):
            
        # Setup logging
        if __name__ == '__main__':
            self.logger=logging.getLogger('{a}.{b}'.format(a=type(self).__name__, b=type(self).__name__))
        else:
            self.logger=logging.getLogger('{a}.{b}'.format(a=__name__, b=type(self).__name__))


        time=[imap_sent_since,imap_sent_before]

        for t in range(len(time)):
            if not isinstance(time[t], (datetime.datetime, datetime.date)):
                if type(time[t]) == str:
                    time[t]=dateutil.parser.isoparse(time[t])

        self.config={}

        # Process configuration
        if config is not None:
            self.config=copy.deepcopy(config)

        lateConfig={}
        lateConfig['imap']={
            'server': imap_server,
            'folder': imap_folder,
            'user': imap_user,
            'password': imap_password,
            'sent_since': time[0],
            'sent_before': time[1]
        }

        lateConfig['smtp']={
            'server': smtp_server,
            'user': smtp_user,
            'password': smtp_password,
        }

        lateConfig['general']={
            'sender': sender,
            'replyto': replyto,

            # The actual text to reply
            'replytxt': replytxt,
            'replyhtml': replyhtml,
            
            'ignore': ignore_list,
            
            'skip': skip_list,
            
            'dryrun': dryrun,
            
            'real_target': target_impersonation_email
        }

        for section in lateConfig.keys():
            if section in self.config:
                self.config[section].update(lateConfig[section])
            else:
                self.config[section]=lateConfig[section]
                
        self.loadReplyMessages()

        self.logger.debug(f"Configuration is: {self.config}")

        self.processor = type(self).__name__

        
        
        

    def loadReplyMessages(self):
        """
        Check if self.config['general']['reply*'] are files and load them in place
        """
        
        if os.access(self.config['general']['replyhtml'], os.R_OK):
            with open(self.config['general']['replyhtml']) as fp:
                self.config['general']['replyhtml']=fp.read()

        if os.access(self.config['general']['replytxt'], os.R_OK):
            with open(self.config['general']['replytxt']) as fp:
                self.config['general']['replytxt']=fp.read()

        
        
    def extractMessageTokens(self, message):
        tokens={}
        
        tokens['from']=message['From']
        tokens['date']=email.utils.parsedate_to_datetime(message['Date'])
        tokens['to']=message['To']
        tokens['replyto']=message['Reply-To']
        tokens['sendername']=''
        tokens['subject']=''

        
        # Decode subject
        
        subjlist=email.header.decode_header(message['Subject'])
        
        for s in subjlist:
            # Decode each part of subject according to its detected encoding
            encoding=s[1] or 'ascii'
            if isinstance(s[0], str):
                tokens['subject']+=s[0]
            else:
                tokens['subject']+=s[0].decode(encoding)
                
        tokens['subject']=tokens['subject'].replace('\n','').replace('\r','')
        
        
        
        # extract full sender name
        
        extractName = r'^(.+)<.*>$'
        formatName = r'(.+),(.+)'

        name = re.search(extractName, message['From'])
        if not name is None:
            tokens['sendername']=name.group(1).replace('"','').replace("'",'')
            nameParts = re.search(formatName, tokens['sendername'])
            if not nameParts is None:
                last=nameParts.group(1).strip()
                first=nameParts.group(2).strip()
                tokens['sendername']=f'{first} {last}'
            tokens['sendername']=tokens['sendername'].strip()
                
                
                
        
        # calculate a hash for this message
        
        idCalc=hashlib.new('shake_256')
        hashText='{}|{}|{}|{}'.format(
            tokens['from'],
            tokens['date'],
            tokens['subject'],
            datetime.datetime.now()
        )
        idCalc.update(hashText.encode('UTF-8'))
        tokens['hash']=idCalc.hexdigest(5)
        
        return tokens
    
    
    
    
    def makeReplyHeader(self, tokens):
        self.logger.debug(tokens)

        headerhtml=self.headerTemplate.format(**tokens)
        headertxt=re.sub('<[^<]+?>', '', headerhtml)

        return headerhtml,headertxt



    def getNextMessage(self):
        self.logger.debug(f"{self.processor} is connecting to IMAP {self.config['imap']['user']}@{self.config['imap']['server']}/{self.config['imap']['folder']}")
                
        M = imaplib.IMAP4_SSL(self.config['imap']['server'])
        M.login(self.config['imap']['user'], self.config['imap']['password'])
        
#         l=M.list()
#         for i in l[1]:
#             self.logger.debug(i)
        
        folderStatus = M.select('\"{}\"'.format(self.config['imap']['folder']))
                
        if folderStatus[0] == 'NO':
            self.logger.warning("Folder {} doesn't exist".format(self.config['imap']['folder']))
            return reports

        
        
        # https://www.atmail.com/blog/advanced-imap/
        # https://gist.github.com/martinrusev/6121028
        # https://www.example-code.com/python/imap_search.asp
        
#         imapSearch=['UNSEEN']
        imapSearch=[]
        
        if 'subject' in self.config['imap']:
            imapSearch.append('SUBJECT "{}"'.format(self.config['imap']['subject']))
        
        if self.config['imap']['sent_since']:
            imapSearch.append('SENTSINCE {}'.format(self.config['imap']['sent_since'].strftime("%d-%b-%Y")))
        
        if self.config['imap']['sent_before']:
            imapSearch.append('SENTBEFORE {}'.format(self.config['imap']['sent_before'].strftime("%d-%b-%Y")))
        
        self.logger.debug("Criteria for mail fetch → {}".format(" ".join(imapSearch)))

        
        # Result for IMAP search will be something like:
        #     UNSEEN SUBJECT "ga_parcelas_atrasadas_clicadas" SENTSINCE 01-Mar-2019 SENTBEFORE 21-Mar-2020 
        typ, data = M.search(None," ".join(imapSearch))
#         typ, data = M.sort('REVERSE DATE','UTF-8'," ".join(imapSearch))
        
        
        attachmentContent=None
        inter=None

        listOfMessages=data[0].decode().split()
        
        for msg in listOfMessages:
            typ, messageRaw = M.fetch(msg, '(RFC822)')
            
            for imapResponsePart in messageRaw:
                if isinstance(imapResponsePart, tuple):
                    message={}
                    message['original'] = email.message_from_bytes(imapResponsePart[1])
                    message['tokens'] = self.extractMessageTokens(message['original'])
                    message['body.txt'] = message['body.html'] = ''
                    replyheaders = self.makeReplyHeader(message['tokens'])
                    
                    for part in message['original'].walk():
                        if (part.get('Content-Disposition')
                            and part.get('Content-Disposition').startswith("attachment")):

                            part.set_payload("Attachment removed: %s (%s, %d bytes)"
                                        %(part.get_filename(), 
                                        part.get_content_type(), 
                                        len(part.get_payload(decode=True))))
                            part.set_type("text/plain")

                            del part["Content-Disposition"]
                            del part["Content-Transfer-Encoding"]

                        if part.get_content_type().startswith("text/plain"):
                            if not message['body.txt']:
                                message['body.txt']=replyheaders[1]
                            message['body.txt']+='\n'
                            message['body.txt']+=part.get_payload(decode=True).decode(part.get_content_charset("utf-8"))

                        elif part.get_content_type().startswith("text/html"):
                            if not message['body.html']:
                                message['body.html']+='<blockquote>'
                                message['body.html']=replyheaders[0]

                            message['body.html']+=part.get_payload(decode=True).decode(part.get_content_charset("utf-8"))
                            message['body.html']+='</blockquote>'

                    if not message['body.txt']:
                        message['body.txt']=None
                    if not message['body.html']:
                        message['body.html']=None
                    
                    yield message

        M.close()
        M.logout()

                            

    def massReply(self):
        self.reportlines=[]
        
        # Walk through all messages in the folder
        for m in self.getNextMessage():
            reportline={}
            
            
            
            
            # Check if we must skip this message and not reply
            
            ignoreme=False
            for ignore in self.config['general']['ignore']:
                # Skip this message if this sender is in the ignore list
                if ignore in m['original']["From"]:
                    ignoreme=True
                    break
                    
            if ignoreme:
                self.logger.debug("Ignoring reply to {ffrom}.".format(ffrom=m['original']['From']))
                continue

            for ignore in self.config['general']['skip']:
                if m['original']['From']==ignore['from'] and m['tokens']['date']==ignore['date'] and m['tokens']["subject"]==ignore['subject']:
                    ignoreme=True
                    break
            
            if ignoreme:
                self.logger.debug("Skiping reply to {ffrom}.".format(ffrom=m['original']['From']))
                continue
            
            
            
            
            
            
            self.logger.debug("Detected message: {date}|{to}|{ffrom}|{replyto}|{subject}".format(
                ffrom=m['original']['From'],
                to=m['original']['To'],
                replyto=m['original']["Reply-To"],
                date=m['tokens']['date'],
                subject=m['tokens']["subject"]
            ))
            


            
            
            
            
            # At this point we decided we'll send a reply. Create message containers:
            
            msg = MIMEMultipart('mixed')
            body = MIMEMultipart('alternative')
            
            
            
            
            
            # Decide about the recipient
            
            realtarget=self.config['general']['real_target'] or m['original']["Reply-To"] or m['original']["From"]
            

            
            
            
            # Prepare an envelop
            
            msg["Subject"]        = "RE: " + m['tokens']["subject"].replace("Re: ", "").replace("RE: ", "").replace("re: ", "")
            msg['To']             = realtarget
            msg['In-Reply-To']    = m['original']["Message-ID"]
            msg['References']     = m['original']["Message-ID"]#+orig["References"].strip()
            msg['Thread-Topic']   = m['original']["Thread-Topic"]
            msg['Thread-Index']   = m['original']["Thread-Index"]
            
            if self.config['general']['sender']:
                msg['From']=self.config['general']['sender']

            if self.config['general']['replyto']:
                msg['Reply-To']=self.config['general']['replyto']
                
                
                
                
                
                
            
            # Prepare a full reply, including original sender text, in 2 versions: TXT and HTML
            
            fullReplyTXT=self.config['general']['replytxt'].format(**m['tokens'])
            fullReplyHTML=self.config['general']['replyhtml'].format(**m['tokens'])

            if m['body.txt']:
                fullReplyTXT+='\n\n\n'+m['body.txt']
                
            if m['body.html']:
                fullReplyHTML+='\n\n\n'+m['body.html']

            
            body.attach(MIMEText(fullReplyTXT, 'plain'))
            body.attach(MIMEText(fullReplyHTML, 'html'))

            msg.attach(body)
            
            
         
            # msg now contains an envelope, the reply and the original message attached. Now send it through SMTP
            
            with smtplib.SMTP(self.config['smtp']['server'], 587) as server:
                server.starttls()
                server.login(self.config['smtp']['user'], self.config['smtp']['password'])
                
                if not self.config['general']['dryrun']:
                    server.sendmail(
                        self.config['smtp']['user'],
                        realtarget,
                        msg.as_string()
                    )
            
            reportline=m['tokens']
            reportline['localtime replyied']=datetime.datetime.now()
            reportline['real target']=realtarget
        
            self.reportlines.append(reportline)
            
        return self.reportlines
        
        
            
