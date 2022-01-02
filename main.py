import io
import json
import os
import re
import zipfile
import base64
from datetime import date, timedelta
from urllib.request import urlopen
import pandas as pd
import matplotlib.pyplot as plt
import requests as requests


SHOW_RESULTS_FOR = 'TEx'


def download_files(files_folder="zip_files/"):
    base_url = 'https://www.congreso.es/opendata/votaciones?p_p_id=votaciones&p_p_lifecycle=0&p_p_state=normal' \
               '&p_p_mode=view&targetLegislatura=XIV&targetDate='
    zip_base_url = 'https://www.congreso.es'
    start_date = date.fromisoformat('2020-02-01')
    end_date = date.today()
    delta = timedelta(days=1)
    while start_date <= end_date:
        print(start_date.strftime("%d/%m/%Y"))
        url = base_url + start_date.strftime("%d/%m/%Y")
        print(url)
        html = urlopen(url)
        text = html.read()
        plaintext = text.decode('utf8')
        zip_link = re.findall("href=[\"\'](.*?VOT.*?\.zip)[\"\']", plaintext)
        if len(zip_link) == 1:
            r = requests.get(zip_base_url + zip_link[0])
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for zipitem in z.infolist():
                if zipitem.filename.endswith('.json'):
                    z.extract(zipitem, "%s" % files_folder)
                    print('Download and extracted ' + zipitem.filename)
        start_date += delta


def process_files(files_folder="zip_files/"):
    grouped_results = {}
    files = os.listdir(files_folder)

    for file in files:
        with open(files_folder + file) as vote_json:
            vote_results = json.load(vote_json)
            collected = {}

            for voto in vote_results['votaciones']:
                fix_mixed_groups(voto)
                if voto['grupo'] in collected:
                    if voto['voto'] in collected[voto['grupo']]:
                        collected[voto['grupo']][voto['voto']] += 1
                    else:
                        collected[voto['grupo']][voto['voto']] = 1
                else:
                    collected[voto['grupo']] = {}
                    collected[voto['grupo']][voto['voto']] = 1
            if len(collected) >= 1:
                grouped_results['%s-%s' % (vote_results['informacion']['sesion'], vote_results['informacion']['numeroVotacion'])] = collected

    df = pd.DataFrame(data=grouped_results)
    df = df.applymap(lambda x: 'missed' if pd.isna(x) else max(x, key=x.get))

    df_same_vote = df.apply(lambda x: x.apply(lambda y: True if df.at[SHOW_RESULTS_FOR, x.name] == y else False))
    df_same_vote = df_same_vote.mean(axis=1).sort_values()
    df_same_vote = df_same_vote.drop(SHOW_RESULTS_FOR)

    df_same_vote_only_valid = df.loc[[SHOW_RESULTS_FOR]]
    df_same_vote_only_valid = df[df_same_vote_only_valid.columns[df_same_vote_only_valid.isin(['Sí', 'No']).all()]]
    df_same_vote_only_valid = df_same_vote_only_valid.apply(lambda x: x.apply(lambda y: True if df.at[SHOW_RESULTS_FOR, x.name] == y else False))
    df_same_vote_only_valid = df_same_vote_only_valid.mean(axis=1).sort_values()
    df_same_vote_only_valid = df_same_vote_only_valid.drop(SHOW_RESULTS_FOR)

    df_vote_type_mean = df.apply(pd.value_counts).sum(axis='columns')
    df_vote_type_mean = df_vote_type_mean.apply(lambda x: x / df_vote_type_mean.sum())

    df_vote_type = df.loc[SHOW_RESULTS_FOR]
    df_vote_type = df_vote_type.value_counts(normalize=True)

    combined = pd.DataFrame({SHOW_RESULTS_FOR: df_vote_type, 'mean': df_vote_type_mean})

    df_same_vote.plot.bar()
    image_same_vote = get_image()

    df_same_vote_only_valid.plot.bar()
    image_same_vot_yes_no = get_image()

    combined.plot.barh()
    image_combined = get_image()
    with open('public/index.html', 'w') as f:
        f.write("""
        <html>
            <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
            
            <h1>Con qué grupos tiene más similitud de voto Teruel Existe</h1>
            {}
            <h1>Cuando vota Sí o No</h1>
            {}
            <h1>Qué vota Teruel Existe</h1>
            {}
            
        </html>
        """.format(image_same_vote, image_same_vot_yes_no, image_combined))


def get_image():
    tmpfile = io.BytesIO()
    plt.savefig(tmpfile, format='png', bbox_inches='tight')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return '<img src=\'data:image/png;base64,{}\'>'.format(encoded)


def fix_mixed_groups(voto):
    if voto['diputado'] == 'Guitarte Gimeno, Tomás': voto['grupo'] = 'TEx'
    if voto['diputado'] == 'Baldoví Roda, Joan': voto['grupo'] = 'Compromís'
    if voto['diputado'] == 'Bel Accensi, Ferran': voto['grupo'] = 'PDeCAT'
    if voto['diputado'] == 'Boadella Esteve, Genís': voto['grupo'] = 'PDeCAT'
    if voto['diputado'] == 'Cañadell Salvia, Concep': voto['grupo'] = 'PDeCAT'
    if voto['diputado'] == 'Miquel i Valentí, Sergi': voto['grupo'] = 'PDeCAT'
    if voto['diputado'] == 'Rego Candamil, Néstor': voto['grupo'] = 'BNG'
    if voto['diputado'] == 'Calvo Gómez, Pilar': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Illamola Dausà, Mariona': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Nogueras i Camero, Míriam': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Pagès i Massó, Josep': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Borràs Castanyer, Laura': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Alonso-Cuevillas i Sayrol, Jaume': voto['grupo'] = 'Junts'
    if voto['diputado'] == 'Errejón Galván, Íñigo': voto['grupo'] = 'MasPaís'
    if voto['diputado'] == 'Sabanés Nadal, Inés': voto['grupo'] = 'MasPaís'
    if voto['diputado'] == 'Botran Pahissa, Albert': voto['grupo'] = 'CUP'
    if voto['diputado'] == 'Vehí Cantenys, Mireia': voto['grupo'] = 'CUP'
    if voto['diputado'] == 'Cambronero Piqueras, Pablo': voto['grupo'] = 'CdsExc'
    if voto['diputado'] == 'García Adanero, Carlos': voto['grupo'] = 'UPN'
    if voto['diputado'] == 'Sayas López, Sergio': voto['grupo'] = 'UPN'
    if voto['diputado'] == 'Martínez Oblanca, Isidro Manuel': voto['grupo'] = 'FAC'
    if voto['diputado'] == 'Mazón Ramos, José María': voto['grupo'] = 'PRC'
    if voto['diputado'] == 'Oramas González-Moro, Ana María': voto['grupo'] = 'CC'
    if voto['diputado'] == 'Quevedo Iturbe, Pedro': voto['grupo'] = 'NC-CCa-PNC'

    # Replaced
    if voto['diputado'] == 'Elorriaga Pisarik, Gabriel': voto['grupo'] = 'GP'
    if voto['diputado'] == 'Tizón Vázquez, Uxía': voto['grupo'] = 'GS'
    if voto['diputado'] == 'González Laso, Natividad': voto['grupo'] = 'GS'
    if voto['diputado'] == 'Taibo Monelos, Diego': voto['grupo'] = 'GS'
    if voto['diputado'] == 'Segura Just, Juan Carlos': voto['grupo'] = 'GVOX'
    if voto['diputado'] == 'Medel Pérez, Rosa María': voto['grupo'] = 'GCUP-EC-GC'
    if voto['diputado'] == 'Pita Cárdenes, María del Carmen': voto['grupo'] = 'GCUP-EC-GC'
    if voto['diputado'] == 'Álvarez i García, Gerard': voto['grupo'] = 'GR'
    if voto['diputado'] == 'López-Bas Valero, Juan Ignacio': voto['grupo'] = 'GCs'
    if voto['diputado'] == 'Jara Moreno, Mercedes': voto['grupo'] = 'GVOX'
    if voto['diputado'] == 'Gutiérrez Vivas, Miguel Ángel': voto['grupo'] = 'GCs'
    if voto['diputado'] == 'Pérez Merino, María Mercedes': voto['grupo'] = 'GCUP-EC-GC'
    if voto['diputado'] == 'Fernández-Roca Suárez, Carlos Hugo': voto['grupo'] = 'GVOX'
    if voto['diputado'] == 'Constenla Carbón, Juan Manuel': voto['grupo'] = 'GP'


if __name__ == '__main__':
    download_files()
    process_files()
