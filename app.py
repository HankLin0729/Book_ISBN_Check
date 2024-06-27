import os
import subprocess
from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import pandas as pd
from datetime import datetime
import openpyxl

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 如果上傳文件夾不存在，則創建它
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 顯示上傳表單
@app.route('/')
def upload_form():
    return render_template('upload.html')

# 處理文件上傳
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
    
    # 使用 ZXing 解碼條形碼
    isbns, debug_infos = decode_barcodes_with_zxing(file_paths)
    return jsonify({'isbns': isbns, 'debug_infos': debug_infos, 'image_paths': [url_for('uploaded_file', filename=os.path.basename(path)) for path in file_paths]})

# 顯示上傳的文件
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 使用 ZXing 解碼條形碼的函數
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
        debug_info = f'Running command: {command}<br>'
        
        try:
            # 執行命令行指令
            process = subprocess.run(command, capture_output=True, text=True, shell=True)
            output = process.stdout
            debug_info += 'Command output:<br>' + output.replace('\n', '<br>')

            raw_isbn = parsed_isbn = None

            for line in output.split('\n'):
                if 'Parsed result' in line:
                    parsed_isbn = line.split(':')[-1].strip()
                if 'Raw result' in line:
                    raw_isbn = line.split(':')[-1].strip()

            isbns.append(raw_isbn or "No Raw ISBN found")
            isbns.append(parsed_isbn or "No Parsed ISBN found")
            
            debug_infos.append(debug_info)
        except subprocess.CalledProcessError as e:
            debug_info += f'Error: {str(e)}<br>'
            debug_infos.append(debug_info)
            isbns.append("Error occurred")

    # 將 ISBN 添加到 Excel 文件中
    add_isbns_to_excel(isbns, debug_infos)
    
    return isbns, debug_infos

# 將 ISBN 添加到 Excel 文件的函數
def add_isbns_to_excel(isbns, debug_infos):
    file_name = 'data.xlsx'
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=['key', 'time', 'isbn', 'debug_info'])
        df.to_excel(file_name, sheet_name='data', index=False, engine='openpyxl')
    
    book = openpyxl.load_workbook(file_name)
    sheet = book['data']
    
    current_key = len(sheet['A'])  
    
    for isbn, debug_info in zip(isbns, debug_infos):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [current_key, current_time, isbn, debug_info]
        sheet.append(new_row)
        current_key += 1
    
    book.save(file_name)

if __name__ == "__main__":
    app.run(debug=True)
