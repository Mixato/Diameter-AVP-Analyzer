import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def parse_diameter_message(message_text):
    """
    Analiza un solo mensaje Diameter del formato de texto proporcionado.
    Devuelve una lista de diccionarios que representan los AVPs con todo su contenido.
    """
    avps = []
    
    # 1. Eliminar los números de línea del texto del mensaje
    message_text_clean = re.sub(r'^\s*\d+\s+-\s+', '', message_text, flags=re.MULTILINE)

    # 2. Expresión regular para capturar cada AVP y su bloque de texto completo.
    avp_pattern = re.compile(r'avpCode:(.+?)\s+\((\d+)\)[\s\S]+?(?=^.*avpCode:|\Z)', re.MULTILINE)
    
    matches = avp_pattern.finditer(message_text_clean)

    for match in matches:
        avp_name = match.group(1).strip()
        avp_code = match.group(2)
        # Captura el bloque de texto completo del AVP, incluyendo cabeceras y datos.
        avp_full_content = match.group(0).strip()
        
        avps.append({
            'name': avp_name,
            'code': avp_code,
            'value': avp_full_content,
            'raw': avp_full_content
        })
    
    # Extracción de los IDs de cabecera
    header_info = {
        'version': re.search(r'version:0x(.+?) \((\d+)\)', message_text),
        'commandFlag': re.search(r'commandFlag[\s\S]+?request:(.+?)\s+proxiable:(.+?)\s+error:(.+?)', message_text),
        'commandCode': re.search(r'cmdCodeR:str \((\d+)\)', message_text),
        'applicationId': re.search(r'applicationId:.+? \((\d+)\)', message_text),
        'hopByHopId': re.search(r'hopByHopId:0x(.+?) \((\d+)\)', message_text),
        'endToEndId': re.search(r'endToEndId:0x(.+?) \((\d+)\)', message_text)
    }

    parsed_data = {
        'header': {},
        'avps': avps
    }
    
    if header_info['version']:
        parsed_data['header']['version'] = header_info['version'].group(2)
    if header_info['commandFlag']:
        flags = header_info['commandFlag']
        parsed_data['header']['commandFlags'] = f"Request: {flags.group(1)}, Proxiable: {flags.group(2)}, Error: {flags.group(3)}"
    if header_info['commandCode']:
        parsed_data['header']['commandCode'] = header_info['commandCode'].group(1)
    if header_info['applicationId']:
        parsed_data['header']['applicationId'] = header_info['applicationId'].group(1)
    if header_info['hopByHopId']:
        parsed_data['header']['hopByHopId'] = header_info['hopByHopId'].group(2)
    if header_info['endToEndId']:
        parsed_data['header']['endToEndId'] = header_info['endToEndId'].group(2)

    return parsed_data

def compare_avps(avps1, avps2):
    """Compara dos listas de AVPs y devuelve una lista de AVPs con diferencias, ignorando el orden."""
    diff_avps = []
    
    avp_map1 = {avp['name']: avp['raw'] for avp in avps1}
    avp_map2 = {avp['name']: avp['raw'] for avp in avps2}

    all_keys = set(avp_map1.keys()) | set(avp_map2.keys())
    
    for key in sorted(all_keys):
        raw1_content = avp_map1.get(key, 'N/A (Falta)')
        raw2_content = avp_map2.get(key, 'N/A (Falta)')
        
        # Separar el contenido por líneas para una comparación más granular
        lines1 = raw1_content.splitlines()
        lines2 = raw2_content.splitlines()
        
        # Crear un nuevo contenido con las líneas marcadas
        marked_raw1 = []
        marked_raw2 = []

        # Usar un zip_longest para comparar hasta que la línea más larga se agote
        from itertools import zip_longest
        has_diff = False
        for line1, line2 in zip_longest(lines1, lines2, fillvalue=''):
            if line1 != line2:
                has_diff = True
                marked_raw1.append(f"-> {line1}")
                marked_raw2.append(f"-> {line2}")
            else:
                marked_raw1.append(line1)
                marked_raw2.append(line2)

        if has_diff:
            diff_avps.append({
                'name': key,
                'raw1': '\n'.join(marked_raw1),
                'raw2': '\n'.join(marked_raw2)
            })
            
    return diff_avps

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message1_text = request.form.get('message1', '').strip()
        message2_text = request.form.get('message2', '').strip()

        if message1_text and message2_text:
            parsed_data1 = parse_diameter_message(message1_text)
            parsed_data2 = parse_diameter_message(message2_text)
            
            diffs = compare_avps(parsed_data1['avps'], parsed_data2['avps'])

            return render_template('index.html', diffs=diffs, 
                                   message1_text=message1_text, 
                                   message2_text=message2_text,
                                   mode='comparison')
        elif message1_text:
            parsed_data = parse_diameter_message(message1_text)
            return render_template('index.html', parsed_data=parsed_data,
                                   message1_text=message1_text, 
                                   mode='single')
        elif message2_text:
            parsed_data = parse_diameter_message(message2_text)
            return render_template('index.html', parsed_data=parsed_data,
                                   message2_text=message2_text, 
                                   mode='single')
        else:
            return render_template('index.html')
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)