from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from google import genai
import PIL.Image
import csv
import os
import base64
import uuid
import numpy as np
import pandas as pd
import shutil

latest_file=''#for download
roll_number=0
folder_name=''

session={
    'user-name': 'wahid7',
    'user-id': 5000
}
image_list=[]
# header_dict={}
final_dict={}
roll_list=[]


#genai.configure(api_key="AIzaSyCQfcVp16z3orGo5DZiP0J6x9giJm0U0Mo")
client = genai.Client(api_key="AIzaSyCQfcVp16z3orGo5DZiP0J6x9giJm0U0Mo")

app = Flask(__name__)
UPLOAD_FOLDER = 'mysite/static/uploads'  # Ensure this directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Serve the camera page
@app.route('/')
def index():
    final_dict.clear()
    return render_template('frontend.html')  # Save this HTML file in the 'templates' folder

# Save an image when received
@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.get_json()
    image_data = data.get('image')

    if image_data.startswith("data:image"):
        _, image_data = image_data.split(',', 1)

    try:
        image_bytes = base64.b64decode(image_data)
        filename = f"{uuid.uuid4().hex}.png"
        image_list.append(filename)
        #filename = f"{session['user-name']}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(image_bytes)
            print(f"saving...{filename}")

        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        print("Error saving image:", e)
        return jsonify({'success': False}), 500

# Process all captured images
@app.route('/process_images', methods=['POST'])
def process_images():
    #folder bana csv rakhar jonno
    global folder_name
    folder_name=f"{uuid.uuid4().hex}"
    os.makedirs(folder_name)
    print("Entered process_images routr/func\n")
    # image_list.clear()
    data = request.get_json()
    image_filenames = data.get('images', [])
    for filename in image_filenames:
        print(filename, end='\n')

    if not image_filenames:
        print("No files\n")
        return jsonify({'success': False, 'error': 'No images received'})

    # Example processing (this can be modified as needed)
    for filename in image_filenames:
        print(f"Processing: {filename}")
        image = PIL.Image.open(f'mysite/static/uploads/{filename}')
        #client = genai.configure(api_key="AIzaSyCQfcVp16z3orGo5DZiP0J6x9giJm0U0Mo")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Generate a proper csv format for the given image", image]
        )
        text_data = response.text

        # save_to_csv(text_data, f'{filename}.csv')





        global roll_number
        response2 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract the 'Roll No. :' from this grade card image. Return only the rollnumber as a single string.", image]
        )


        if response2.text:
            lines=response2.text.split('\n')
        for line in lines:
            if "Roll No.: " in line:
                roll_number=line.split(":")[-1].strip()
                roll_number=''.join(filter(str.isdigit, roll_number))
                print("roll if\n")
            else:
                roll_number=''.join(filter(str.isdigit, response2.text))
        roll_number=int(roll_number.strip().replace(" ", ""))
        print(f"roll is: {roll_number}\ntype: ")
        print(type(roll_number), end='\n')

        # response3 = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     contents=["Extract the Session(range of year) from this grade card image. Return as a single string.", image]
        # )
        # sess=response3.text
        # print(f"session is: {sess}\n")

        response4 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract the Year(1st year or 2nd year etc) from this grade card image. Return as a single integer digit", image]
        )
        year=int(response4.text)
        print(f"year is: {year}\n")
        print(type(year), end="\n")

        response5 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract the Semester(1st or 2nd) from this grade card image. Return as a single integer digit", image]
        )
        sem=int(response5.text)
        sem='1st' if sem==1 else '2nd'
        print(f"semester is: {sem}\n")
        print(type(sem), end="\n")

        response6 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract the Department and shorten it(if 'Computer Science specialisation Artificial intelligence and Machine Learning' then 'CSE-AIML' and likewise') from this grade card image. Return as a single string", image]
        )
        dept=response6.text
        print(f"dept is: {dept}\n")
        print(type(dept), end="\n")

        response7 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract the SGPA(Semester Grade Point Average) from this grade card image. Return as a string", image]
        )
        sgpa=float(response7.text.strip().replace(" ", "").replace('"', ' '))
        print(f"sgpa is: {sgpa}\n")
        print(type(sgpa), end="\n")

        response3 = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"Extract the Session(range of year) from this grade card image, its the year during which the examination of {year} year, {sem} semester took place. Return as a single string.", image]
        )
        sess=response3.text
        print(f"session is: {sess}\n")

        save_to_csv(text_data, (sess, year, sem, dept, roll_number),sgpa, f'{filename}.csv')






    return jsonify({'success': True})






def save_to_csv(text,tup,sgpa, filename="output.csv"):
    lines = text.strip().split("\n")
    # header=lines[1]
    # print("header is: ")
    # print(header,end='\n')
    # print(f"stored dict keys: {header_dict.keys()}")
    tup2_no_roll=tup[:4]
    roll=tup[-1]
    is_subset=any(set(tup2_no_roll).issubset(set(key)) for key in final_dict.keys())
    print(is_subset, end='\n')
    print(f'dict before condition\n{final_dict}')
    if tup in final_dict: #check for full match with roll
        # its a repeat case ignore exit
        print("if\n")
        return
    elif is_subset: #it means everything same except roll (new user for same file type)
        # append to mapped file name exit
        print("else if\n")
        for tups in final_dict:
            if set(tup2_no_roll).issubset(set(tups)):
                found_tup=tups

        #create csv  then restructure then append
        data = [line.split(",") for line in lines]
        data=data[1:-2]
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"CSV file '{filename}' created successfully.\n")
        #restructure
        df=pd.read_csv(filename)
        df=df.dropna()
        print(df, end='\n')
        df=df.iloc[:, [0,-1]]
        df=df.T
        print(df, end="\n")
        # df.insert(0,'Roll',[roll_number, '99'])
        print(df, end="\n")
        file_name=f'{uuid.uuid4().hex}.csv'
        df.to_csv(file_name, index=False, header=False)
        print(f"roll no: {roll_number}\n")
        print(f'{file_name} before insering roll\n')
        df=pd.read_csv(file_name)
        df.insert(0,'Roll',[roll])
        df['SGPA']=sgpa
        file_name=f'{uuid.uuid4().hex}.csv'
        df.to_csv(file_name,index=False)

        print("appending\n")

        print("existing keys are: \n")
        print(final_dict, end='\n')
        data = [line.split(",") for line in lines]#text into list of rows
        data=data[2:-2]
        filename=final_dict[found_tup]
        print(f'227, {folder_name}/{filename}\n')
        df1=pd.read_csv(folder_name+'/'+filename)
        os.remove(folder_name+'/'+filename)
        df2=pd.read_csv(file_name)
        print(df1,end='\n')
        print(df2,end='\n')

        df_combined=pd.concat([df1, df2], axis=0, ignore_index=True)
        #df_combined.to_csv('test.csv', index=False)
        df_combined.to_csv(os.path.join(folder_name, f"{uuid.uuid4().hex}.csv"), index=False)

        # with open(filename, "a", newline="", encoding="utf-8") as file:
        #     writer = csv.writer(file)
        #     writer.writerows(data)
        # print(f"CSV file '{filename}' appended successfully.\n")
    else:
        # create a new csv file and map to  in final_dict
        # add tup to final_dict
        print("else")
        print("add header to dict\n")
        print(f'new tuple is: {tup}\n')
        final_dict[tup]=filename
        data = [line.split(",") for line in lines]
        data=data[1:-2]
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"CSV file '{filename}' created successfully.\n")
        #restructure
        df=pd.read_csv(filename)
        os.remove(filename)
        df=df.dropna()
        print(df, end='\n')
        df=df.iloc[:, [0,-1]]
        df=df.T
        print(df, end="\n")
        # df.insert(0,'Roll',[roll_number, '99'])
        print(df, end="\n")
        file_name=f'{uuid.uuid4().hex}.csv'
        df.to_csv(file_name, index=False, header=False)
        print(f"roll no: {roll_number}\n")
        print(f'{file_name} before insering roll\n')
        df=pd.read_csv(file_name)
        os.remove(file_name)
        df.insert(0,'Roll',[roll])
        df['SGPA']=sgpa
        file_name=f'{uuid.uuid4().hex}.csv'
        #df.to_csv(file_name,index=False)


        df.to_csv(os.path.join(folder_name, file_name), index=False)


        global latest_file
        latest_file=file_name
        final_dict[tup]=file_name
        print(file_name, end='\n')
        print(f'latest file:{latest_file}\n')


@app.route('/download')
def download():
    global folder_name
    final_download_file=''
    if len(os.listdir(folder_name))>1:
        final_download_file=f'{uuid.uuid4().hex}'
        shutil.make_archive("csv_zip_storage/"+final_download_file, 'zip', folder_name)
        final_download_file+='.zip'
        return send_file("csv_zip_storage/"+final_download_file,mimetype="application/zip", as_attachment=True)

    final_download_file=os.listdir(folder_name)[0]
    print(f'file name: {final_download_file}\n')
    return send_file(folder_name+'/'+final_download_file,mimetype="text/csv", as_attachment=True)
    global latest_file
    print(f"attempting download of {latest_file}...\n")

    return send_file(latest_file,mimetype="text/csv", as_attachment=True)
if __name__ == '__main__':
    app.run(debug=False)
