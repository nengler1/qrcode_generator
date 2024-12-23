import qrcode

qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=1,
)
vcard = """BEGIN:VCARD
VERSION:3.0
N:Gump;Forrest
FN:Forrest Gump
ORG:Bubba Gump Shrimp Co.
TITLE:Shrimp
TEL;TYPE=WORK,VOICE:(111) 555-1212
EMAIL;TYPE=PREF,INTERNET:fgump@example.com
URL:https://example.com
REV:20080424T195243Z
END:VCARD"""

qr.add_data(vcard)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

img.save("qrcode_vcard.png")