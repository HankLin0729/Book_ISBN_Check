from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import subprocess
import os
import pandas as pd
from datetime import datetime
import openpyxl

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'isbns': [], 'debug_infos': ['No file part in the request'], 'image_paths': []})
    files = request.files.getlist('file')
    file_paths = []
    for file in files:
        if file and file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)
    isbns, debug_infos = decode_barcodes_with_zxing(file_paths)
    return jsonify({'isbns': isbns, 'debug_infos': debug_infos, 'image_paths': [url_for('uploaded_file', filename=os.path.basename(path)) for path in file_paths]})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def decode_barcodes_with_zxing(image_paths):
    zxing_core_jar = os.path.join('libs', 'core-3.4.0.jar')
    zxing_javase_jar = os.path.join('libs', 'javase-3.4.0.jar')
    jcommander_jar = os.path.join('libs', 'jcommander-1.81.jar')
    isbns = []
    debug_infos = []

    for image_path in image_paths:
        abs_image_path = os.path.abspath(image_path).replace("\\", "/")
        formatted_image_path = 'file:/' + abs_image_path
        
        command = f'java -cp "{zxing_core_jar};{zxing_javase_jar};{jcommander_jar}" com.google.zxing.client.j2se.CommandLineRunner "{formatted_image_path}"'
        debug_info = 'Running command: ' + command + '<br>'
        
        process = subprocess.run(command, capture_output=True, text=True, shell=True)
        output = process.stdout
        debug_info += 'Command output:<br>' + output.replace('\n', '<br>')
        
        parsed_isbn = None
        raw_isbn = None
        
        for line in output.split('\n'):
            if line.startswith('Parsed result'):
                parsed_isbn = line.split(':')[-1].strip()
            elif line.startswith('Raw result'):
                raw_isbn = line.split(':')[-1].strip()

        if raw_isbn:
            isbns.append(raw_isbn)
        else:
            isbns.append("No Raw ISBN found")
        
        if parsed_isbn:
            isbns.append(parsed_isbn)
        else:
            isbns.append("No Parsed ISBN found")
        
        debug_infos.append(debug_info)
    
    add_isbns_to_excel(isbns, debug_infos)
    
    return isbns, debug_infos

def add_isbns_to_excel(isbns, debug_infos):
    file_name = 'data.xlsx'
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=['key', 'time', 'isbn'])
        df.to_excel(file_name, sheet_name='data', index=False, engine='openpyxl')
    
    book = openpyxl.load_workbook(file_name)
    sheet = book['data']
    
    current_key = len(sheet['A'])  
    
    for isbn, debug_info in zip(isbns, debug_infos):
        new_key = current_key
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [new_key, current_time,debug_info]
        sheet.append(new_row)
        current_key += 1
    
    book.save(file_name)

if __name__ == "__main__":
    app.run(debug=True)
