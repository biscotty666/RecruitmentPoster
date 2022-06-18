# !/usr/bin/python

#Prepare environment
import PIL.ImageDraw
import discord
import os
import regex
import yaml
import time
from swgohhelp import SWGOHhelp, settings
from reportlab.pdfgen import canvas, pdfimages
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, cm
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from PIL import Image, ImageDraw

# Prepare custom fonts
pdfmetrics.registerFont(TTFont('Trickster', 'Trickster-Reg.ttf'))
pdfmetrics.registerFont(TTFont('Vampire', 'Vampire Wars.ttf'))

# Fetch configuration variables
with open('venv/config.yml') as file :
    config = yaml.safe_load(file)

#Fetch guild data from game. From the raw data populate guilds

# Function to process raid information and pass RDict back to modify guilds
def PRaidCounts(RDict) :
    RDict['rancor'] = RDict['rancor'][-2:]
    RDict['aat'] = RDict['aat'][-2:]
    RDict['sith_raid'] = RDict['sith_raid'][-2:]
    if 'rancor_challenge' in RDict :
        RDict['rancor_challenge'] = RDict['rancor_challenge'][-2:]
    return RDict

#Make the connection
creds = settings(config['CredName'], config['CredPass'], config['CredNum'], config['CredLet'])
client = SWGOHhelp(creds)
#Fetch the data
guilds = []
counter = 0
for allycode in config['allycodes'] :
    counter += 1
    print('This is pass ', counter, '/14')
    def GetData():
        try:
            print('Trying')
            response = client.get_data('guild', allycode)
            if response == ' None ':
                GetData()
            return response
        except Exception as e:
            time.sleep(15)
            GetData()

    response = GetData()
    # print('Got response: "', response, '"')
    # extract dictionary from list
    guildinfo = response[0]
    # Call function to populate raid items in guilds
    RDict = PRaidCounts(guildinfo['raid'])
    # Add the rest of the info
    guilds.append({
        'GGp' : guildinfo['gp'],
        'GName' : guildinfo['name'],
        'GMembers' : guildinfo['members'],
        'GRaid' : guildinfo['raid'],
    })

#populate Canvas

#Create the Canvas object
c = canvas.Canvas(config['RSFilename'])
width = 640
height = 360
c.setPageSize((width, height))
c.setTitle(config['RSTitle'])
def background(c):
    c.setFillColorRGB(1,0,0)
    c.rect(5,5,652,792,fill=1)

# background(c)
# c.translate(width/2, height/2)

#add the title to the image
c.setFont(config['Font'], config['FontSize'])
docTitle = str(config['RSDocumentTitle']).replace('??','ø')

# prepare images to be added to first row

# c.drawImage('GuildLogo_Transparent.png',210,60)
c.drawCentredString(320, 330, docTitle)


#populate data for the table
#create first row of table
data= [['', 'GP','DSTB', 'LSTB', 'CPit', 'WAT', 'KAM', 'GM']]
#create the rest of the rows
for guild in guilds :
    #modify appearance and content of items in guilds
    GPRounded = str(round(guild['GGp']/1000000))

    # This is to change the returned name into the name as printed
    # on the poster
    def GNameModify(name):
       # Remove the word Phantom and any of it's permutations
        name = regex.sub(r'Phant[oø?]+m\s*?', '', str(guild['GName']), 1)
       # Remove leading space
        name = regex.sub(r'^ ', '', name, 1)
       # Special bonus for Limb
        name = regex.sub(r'\?\?', 'i', name, 1)
        return name

    GNameModified = GNameModify('GName')
    DSTB = config['DSTB'][GNameModified]
    LSTB = config['LSTB'][GNameModified]
    CPIT = config['CPIT'][GNameModified]
    WAT = config['WAT'][GNameModified]
    KAM = config['KAM'][GNameModified]

    #create table row
    data.append([GNameModified, GPRounded, DSTB, LSTB, CPIT, WAT, KAM, guild['GMembers']])

#create Table object based on data and add to image
table = Table(data, colWidths=[130,70,70,70,70,70,70], rowHeights=20)
table.setStyle(TableStyle([
    ('FONT',(0,0),(-1,-1), 'Helvetica', 20),
    ('BOTTOMPADDING',(0,0),(-1,0),10),
    ('FONTSIZE',(0,0),(-1,0),16),
    ('FONTSIZE',(0,1),(0,-1),14),
    ('FONTSIZE',(1,1),(-1,-1),12),
    # ('ALIGN',(1,1), (1,-1),'RIGHT'),
    ('ALIGN',(1,0), (-1,-1),'CENTER'),
    ('TEXTCOLOR',(0,0),(-1,-1),colors.firebrick),
    ]))
table.wrapOn(c, width, height)
table.drawOn(c, 8, 5)

c.showPage()
c.save()
