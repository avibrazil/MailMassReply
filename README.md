# Mass-reply all e-mail message on an IMAP folder

Reply messages can be personalized.

## Usage
```python
import mailmassreply
import logging

logging.basicConfig(level=logging.DEBUG)

a=mailmassreply.MailMassReply(
    replytxt='example-reply.txt',
    replyhtml='example-reply.html',
    
    sender='you@gmail.com (Avi Alkalay, senior data engineer & scientist)',
    replyto='you+massreply@gmail.com (Avi Alkalay, senior data engineer & scientist)',
    
    ignore_list=['mail1@domain.com','mail2@domain.com'],
    
    skip_list=ignore,
    
    imap_server='imap.gmail.com',
    imap_user="you@gmail.com",
    imap_password="jdl.....sfvu",

    imap_folder='Folder to scan and mass reply',
    
    smtp_server='smtp.gmail.com',
    smtp_user="you@gmail.com",
    smtp_password="jdl.....sfvu",
    
    dryrun=False,
)

dirtyreport=a.massReply()
```

The `MailMassReply` class gets a long list of parameters becase it automates a lot of actions:

1. Connect to your IMAP server with your credentials (`imap_*` parameters)
2. Scan a specific folder (`imap_folder`)
3. For each e-mail message it finds there, extracts tokens as sender name, e-mail address, message subject, message body etc
4. Then build a reply for each and every message attaching the original message (as a regular e-mail client does)
5. Use the template files passed on parameters `replytxt` and `replyhtml` and substitute tokens with what was extracted from original message
6. Send the actual unique replys through your SMTP server (`smtp_*` parameters). Use `sender` and `replyto` as the person that is replying. Ignore and don't reply messages that appear in `ignore_list`.

See [example-usage.ipynb] Jupyter notebook for more.

## Example of reply templates

Templates are the engine for personalized replys.
Templates can be HTML or TXT or both. This is how reply templates look like:

A template for a pure text reply:
<pre>
Hello {sendername}

This message was sent to you because your message to me was put into an IMAP folder on the recepient.

Here is a list of tokens that can be used throughout the message body (as `{{token}}`) that were extracted from the original message:

- from
- date
- to
- replyto
- sendername
- subject
- hash - unique hash calculated from sender, date, subject; can be used on links to track interactions.

So I'll use them to create a personalized phrase like this:

This is a reply to a message from {from}, sent on {date} to {to} and asking for reply on {replyto}.

Best,
Avi Alkalay</pre>

And a template for an HTML reply:

```html
<p>Hello {sendername}</p>

<p>This message was sent to you because your message to me was put into an IMAP folder on the recepient.</p>

Here is a list of tokens that can be used throughout the message body (as `{{token}}`) that were extracted from the original message:

<ul>
    <li>from</li>
    <li>date</li>
    <li>to</li>
    <li>replyto</li>
    <li>sendername</li>
    <li>subject</li>
    <li>hash - unique hash calculated from sender, date, subject; can be used on links to track interactions.</li>
</ul>

<p>So I'll use them to create a personalized phrase like this:</p>

<p>This is a reply to a message from {from}, sent on {date} to {to} and asking for reply on {replyto}.<p>

<p>Best,<br/>
Avi Alkalay</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
```

## Donate if you think I deserve

Please consider donation of any amount in Bitcoin or Ethereum:

* Bitcoin donation: bc1qerzyzwdnsmpfdkl3lcjgm3rhvvy7svy0p89ndj
* Ethereum donation: 0x098dADeDDf14382F19d4F5d989fD8734376B0224
