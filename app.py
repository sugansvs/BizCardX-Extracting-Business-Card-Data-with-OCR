import easyocr
import cv2
import pandas as pd
import re
import sqlite3
import streamlit as st
# Establishing connection to database
conn = sqlite3.connect('card_details.db', check_same_thread=False)
cursor = conn.cursor()
# Creating table in sql
table_create_sql = 'CREATE TABLE IF NOT EXISTS mytable (ID INTEGER PRIMARY KEY AUTOINCREMENT,Name TEXT,Designation TEXT,Company_name TEXT,Address TEXT,Contact_number TEXT,Mail_id TEXT,Website_link TEXT,Image BLOB);'
cursor.execute(table_create_sql)

def upload_database(image):
    # Getting data from image using easyocr
    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image, paragraph=True, decoder='wordbeamsearch')
    # converting got data to single string
    data = []
    j = 0
    for i in result:
        data.append(result[j][1])
        j += 1
    data
    org_reg = " ".join(data)
    reg = " ".join(data)
    # Separating EMAIL
    email_regex = re.compile(r'''(
	[a-zA-z0-9]+
	@
	[a-zA-z0-9]+
	\.[a-zA-Z]{2,10}
	)''', re.VERBOSE)
    email = ''
    for i in email_regex.findall(reg):
        email += i
        reg = reg.replace(i, '')
    # Separating phone number
    phoneNumber_regex = re.compile(r'\+*\d{2,3}-\d{3,10}-\d{3,10}')
    phone_no = ''
    for numbers in phoneNumber_regex.findall(reg):
        phone_no = phone_no + ' ' + numbers
        reg = reg.replace(numbers, '')
    # Separating Address
    address_regex = re.compile(r'\d{2,4}.+\d{6}')
    address = ''
    for addr in address_regex.findall(reg):
        address += addr
        reg = reg.replace(addr, '')
    # Separating website link
    link_regex = re.compile(r'www.?[\w.]+', re.IGNORECASE)
    link = ''
    for lin in link_regex.findall(reg):
        link += lin
        reg = reg.replace(lin, '')
    # Separating Designation (only suitable for this dataset
    desig_list = ['DATA MANAGER', 'CEO & FOUNDER',
                  'General Manager', 'Marketing Executive', 'Technical Manager']
    designation = ''
    for i in desig_list:
        if re.search(i, reg):
            designation += i
            reg = reg.replace(i, '')
    # Separating Company name (only suitable for this dataset)
    # to overcome this combine all the three datas to single column 
    comp_name_list = ['selva digitals', 'GLOBAL INSURANCE',
                      'BORCELLE AIRLINES', 'Family Restaurant', 'Sun Electricals']
    company_name = ''
    for i in comp_name_list:
        if re.search(i, reg, flags=re.IGNORECASE):
            company_name += i
            reg = reg.replace(i, '')
    name = reg.strip()

    # reading and getting byte values of image
    with open(image, 'rb') as file:
        blobimg = file.read()
    # inserting data into table
    image_insert = 'INSERT INTO mytable (Name, Designation, Company_name, Address, Contact_number,Mail_id,Website_link,Image) VALUES (?,?,?,?,?,?,?,?);'
    cursor.execute(image_insert, (name, designation, company_name,
                   address, phone_no, email, link, blobimg))
    conn.commit()
 
def extracted_data(image):
    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image, paragraph=True, decoder='wordbeamsearch')
    img = cv2.imread(image)
    for detection in result:
        top_left = tuple([int(val) for val in detection[0][0]])
        bottom_right = tuple([int(val) for val in detection[0][2]])
        text = detection[1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        img = cv2.rectangle(img, top_left, bottom_right, (204, 0, 34), 5)
        img = cv2.putText(img, text, top_left, font, 0.8,
                          (0, 0, 255), 2, cv2.LINE_AA)
    return img

def show_database():
    new_df = pd.read_sql("SELECT * FROM mytable", con=conn)
    return new_df


# setting page configuration in streamlit
st.set_page_config(page_title='Bizcardx Extraction', layout="wide")

st.balloons()
st.title(':violet[Bizcardx Data Extraction🖼️]')

data_extraction, database_side = st.tabs(
    ['Data uploading and Viewing', 'Database side'])
file_name = 'sugan'
with data_extraction:
    st.markdown(
        "![Alt Text](https://i.gifer.com/3OdB.gif)")
    st.subheader(':violet[Choose image file to extract data]')
    #  Uploading file to streamlit app 
    uploaded = st.file_uploader('Choose a image file')
    #  Convert binary values of image to IMAGE 
    if uploaded is not None:
        with open(f'{file_name}.png', 'wb') as f:
            f.write(uploaded.getvalue())
        # Extracting data from image (Image view)
        st.subheader(':violet[Image view of Data]')
        if st.button('Extract Data from Image'):
            extracted = extracted_data(f'{file_name}.png')
            st.image(extracted)

        # upload data to database
        st.subheader(':violet[Upload extracted to Database]')
        if st.button('Upload data'):
            upload_database(f'{file_name}.png')
            st.success('Data uploaded to Database successfully!', icon="✅")
            
# getting data from database and storing in df variable
df = show_database()
with database_side:
    st.markdown(
        "![Alt Text](https://i.gifer.com/75ez.gif)")
    
    # Showing all datas in database
    st.title(':violet[All Data in Database]')
    if st.button('Show All'):
        st.dataframe(df)

    # Search data in the database
    st.subheader(':violet[Search Data by Column]')
    column = str(st.radio('Select column to search', ('Name', 'Designation',
                 'Company_name', 'Address', 'Contact_number', 'Mail_id', 'Website_link'), horizontal=True))
    value = str(st.selectbox('Please select value to search', df[column]))
    if st.button('Search Data'):
        st.dataframe(df[df[column] == value])