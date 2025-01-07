from flask import Flask, render_template, request, send_file
from markitdown import MarkItDown
import os
from pathlib import Path
import tempfile
import zipfile
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return 'No files selected', 400

    # Create a memory file for the ZIP archive
    memory_file = io.BytesIO()
    
    # Create the ZIP file
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            # Save uploaded file temporarily
            temp_path = Path(app.config['UPLOAD_FOLDER']) / file.filename
            file.save(temp_path)
            
            # Define output path
            output_path = temp_path.with_suffix('.md')
            
            try:
                # Convert file to markdown
                md = MarkItDown()
                result = md.convert(str(temp_path))
                
                # Write the markdown content to the ZIP file
                zf.writestr(
                    f"{Path(file.filename).stem}.md",
                    result.text_content
                )
                
            except Exception as e:
                # Clean up files
                if temp_path.exists():
                    temp_path.unlink()
                if output_path.exists():
                    output_path.unlink()
                    
                # Return error message
                error_msg = str(e)
                if "UnsupportedFormatException" in error_msg:
                    return f'Unsupported format for file {file.filename}. Please upload supported file types.', 400
                return f'Error converting file {file.filename}: {error_msg}', 500
            
            finally:
                # Cleanup temporary files
                if temp_path.exists():
                    temp_path.unlink()
                if output_path.exists():
                    output_path.unlink()
    
    # Prepare the ZIP file for download
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_files.zip'
    )

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)
