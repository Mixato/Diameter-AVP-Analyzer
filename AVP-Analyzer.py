import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def parse_diameter_message(message_text):
    """
    Analiza un solo mensaje Diameter del formato de texto proporcionado.
    Devuelve una lista de diccionarios que representan los AVPs con todo su contenido.
    """
    avps = []
    
    # Expresión regular para capturar cada AVP y su bloque de texto completo.
    avp_pattern = re.compile(r'avpCode:(.+?)\s+\((\d+)\)[\s\S]+?(?=^.*avpCode:|\Z)', re.MULTILINE)
    
    matches = avp_pattern.finditer(message_text)

    for match in matches:
        avp_name = match.group(1).strip()
        avp_code = match.group(2)
        # Captura el bloque de texto completo del AVP, incluyendo cabeceras y datos.
        avp_full_content = match.group(0).strip()
        
        avps.append({
            'name': avp_name,
            'code': avp_code,
            'value': avp_full_content, # Se usa el contenido completo como valor
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
    """Compara dos listas de AVPs y devuelve una lista de AVPs con diferencias."""
    diff_avps = []
    avp_map1 = {avp['name']: avp['raw'] for avp in avps1}
    avp_map2 = {avp['name']: avp['raw'] for avp in avps2}

    all_keys = set(avp_map1.keys()) | set(avp_map2.keys())
    
    for key in sorted(all_keys):
        raw1 = avp_map1.get(key, 'N/A (Falta)')
        raw2 = avp_map2.get(key, 'N/A (Falta)')

        if raw1 != raw2:
            diff_avps.append({
                'name': key,
                'raw1': raw1,
                'raw2': raw2
            })
    return diff_avps

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message1_text = request.form.get('message1', '').strip()
        message2_text = request.form.get('message2', '').strip()

        if message1_text and message2_text:
            # Caso 1: Comparar dos mensajes
            parsed_data1 = parse_diameter_message(message1_text)
            parsed_data2 = parse_diameter_message(message2_text)
            
            diffs = compare_avps(parsed_data1['avps'], parsed_data2['avps'])

            return render_template('index.html', diffs=diffs, 
                                   message1_text=message1_text, 
                                   message2_text=message2_text,
                                   mode='comparison')
        elif message1_text:
            # Caso 2: Mostrar un solo mensaje (Mensaje 1)
            parsed_data = parse_diameter_message(message1_text)
            return render_template('index.html', parsed_data=parsed_data,
                                   message1_text=message1_text, 
                                   mode='single')
        elif message2_text:
            # Caso 3: Mostrar un solo mensaje (Mensaje 2)
            parsed_data = parse_diameter_message(message2_text)
            return render_template('index.html', parsed_data=parsed_data,
                                   message2_text=message2_text, 
                                   mode='single')
        else:
            # No hay mensajes para analizar
            return render_template('index.html')
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)