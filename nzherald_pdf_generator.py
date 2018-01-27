import datetime
import yaml, json, re
import email
import io
import img2pdf

import requests

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class NZHeraldEdition:
    def __init__(self, date, heraldsess):
        self.date = date.strftime("%Y-%m-%d")
        self.heraldsess = heraldsess

        herald_edition_json = 'http://digitaledition.nzme.co.nz/olive/odn/nzherald/get/APNHER-%s/prxml.ashx?kind=doc'
        metadata = heraldsess.get(herald_edition_json % self.date).content
        metadata = json.loads(metadata)
        self.pagecount = metadata['pagesCount']
        self.sections_pages = {}
        for section in metadata['sections']:
            self.sections_pages[section['name']] = range(section['pages'][0], section['pages'][0]+section['pages'][1])
        print("Debug: %d pages and %d sections in today's edition." % (self.pagecount, len(self.sections_pages)))
        self.pages = [None] * self.pagecount

    def fetch_content(self):
        for page_num in range(1, self.pagecount+1):
            page_image_url = 'http://digitaledition.nzme.co.nz/olive/odn/nzherald/get/APNHER-%s/image.ashx?kind=page&page=%d'
            print("Debug: Fetching %s" % (page_image_url % (self.date, page_num)))
            page_png_data = self.heraldsess.get(page_image_url % (self.date, page_num)).content
            self.pages[page_num-1] = page_png_data
    
    def render_pdf(self, page_numbers):
        page_set = [None] * len(page_numbers)
        for i in range(len(page_numbers)):
            page_set[i] = self.pages[page_numbers[i]-1]
        pdf_rawdata = io.BytesIO()
        pdfcfg_pagesize = (841.8897, 1190.551)
        pdfcfg_imgsize = None
        pdfcfg_border = None
        pdfcfg_fit = img2pdf.FitMode.into
        pdfcfg_auto_orient = None
        layout_func = img2pdf.get_layout_fun(pdfcfg_pagesize, pdfcfg_imgsize, pdfcfg_border,
                                             pdfcfg_fit, pdfcfg_auto_orient)
        pdf_rawdata = img2pdf.convert(page_set, title="NZ Herald - %s" % self.date,
                        layout_fun=layout_func)
        return pdf_rawdata

def init():
    config = yaml.load(open('config.yml', 'r'))
    sections_to_exclude = [ t.upper() for t in config['sections_to_exclude'] ]
    session = requests.Session()
    herald_de_url = 'http://digitaledition.nzme.co.nz/Olive/ODN/NZHerald/Default.aspx'
    herald_de_login_url = 'https://nzherald.digitaledition.nzme.co.nz/fnc_login.php'
    herald_postlogin_url = 'https://nzherald.digitaledition.nzme.co.nz/gotopaper2.php'

    # Start auth process
    session.get(herald_de_url)

    # Submit login form data.
    login_data = {'action': 'normallogin',
                  'femail': config['login_email'],
                  'fpassword': config['login_password']}
    session.post(herald_de_login_url, data=login_data)

    # Pretend to be a browser...
    postlogin_data = session.get(herald_postlogin_url)
    postlogin_url2 = re.match('.*document.location.replace\\(\'(.*)\'\\)', postlogin_data.content.decode('utf-8')).groups(0)[0]
    result = session.get(postlogin_url2)

    if result.status_code == 200:
        print("Successfully logged in. Fetching today's edition...")
        nzh_today = NZHeraldEdition(datetime.datetime.now(), session)
        nzh_today.fetch_content()
        pdf_sections = {}
        for section, pages in nzh_today.sections_pages.items():
            if not section.upper() in sections_to_exclude:
                print("Debug: Rendering PDF for section %s" % section)
                pdf_sections[section] = nzh_today.render_pdf(pages)
        
        print("Debug: Creating email message")
        mailmsg = MIMEMultipart()
        mailmsg['Subject'] = 'NZ Herald Digital Edition PDF'
        mailmsg['From'] = config['from_email']
        mailmsg['To'] = config['to_email']
        body = "Hi,\n\nAttached are copies of each section of this morning's NZ Herald.\n\nThis email was sent automatically, please do not reply."
        part1 = MIMEText(body, 'plain')
        mailmsg.attach(part1)

        for section_name, data in pdf_sections.items():
            print("Debug: Attaching %s..." % section_name)
            pdf = MIMEApplication(data, _subtype = "pdf")
            pdf.add_header('Content-Disposition', 'attachment', filename=section_name+".pdf")
            mailmsg.attach(pdf)
        
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.ehlo()
        server.starttls()
        server.send_message(mailmsg)
    else:
        print("Error: Unable to log in!")
        nzh_today = None

if __name__ == "__main__":
    init()
