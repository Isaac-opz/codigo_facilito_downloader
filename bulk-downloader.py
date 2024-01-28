import click
import subprocess
from utils import *
from facilito import Facilito
from playwright.sync_api import sync_playwright, Playwright
import os
import json

class Downloader:
    
    def __init__(self, external_downloader: str, quality: str):
        self.external_downloader = external_downloader
        self.quality = quality
        self.cookies = 'cookies.txt'
        self.cookies_copy = 'cookies_copy.txt'
        self.data_path  = 'data.json'
        self.data = {}
        self.data_dir = 'data'

    def m3u8_downloader(self, file_path, url, ext_dwl):
        """
        external_downloader: str <- 'yt-dlp', 'aria2'
        format_selection: str <- 'bv[height<=quality]+ba/b[height<=quality]'
        """
        if (self.quality == 'best'):
            self.format_selection = 'bv+ba/b'
        else:
            self.format_selection = f'bv[height<={self.quality}]+ba/b[height<={self.quality}]'

        # FIXME: cookies.txt is overwritten automatically with aria2
        # This is a temporary solution
        copy_file(self.cookies, self.cookies_copy)
        
        if (ext_dwl =='yt-dlp'):
            command = ['yt-dlp', '-f', self.format_selection, '--cookies', self.cookies_copy, '-o', f'{file_path}.%(ext)s', '-N', '10', url]
        elif (ext_dwl =='aria2'):
            command = ['yt-dlp', '-f', self.format_selection, '--cookies', self.cookies_copy, '-o', f'{file_path}.%(ext)s', '--external-downloader', 'aria2c', '--external-downloader-args', '-s 10 -x 10 -k 1M', url]
        subprocess.run(command, check=True)
    
    def dl_course(self, course, file_name):
        course_name = course['name']
        content = course['content']

        j, k = 1, len(content)
        for item in content:
            url = item['m3u8']
            group = item['group']
            title = item['title']
            dir_path = f'{course_name}/{group}'
            file_path = f'{dir_path}/{j}. {title}'
            check_path(dir_path)

            if(url is None):
                print(f'[{j} / {k}][reading] {title}')
            else:
                print(f'[{j} / {k}][streaming] {title}')
                self.m3u8_downloader(file_path = file_path, url=url, ext_dwl=self.external_downloader)
            
            j = j + 1
        
        check_path('downloads')
        copy_file(f'data/{file_name}', course_name)
        #move_folder(course_name, 'downloads')

    def bulk_download(self):
        # Obtiene la lista de archivos en el directorio actual
        archivos = os.listdir(self.data_dir)
        # Filtra solo los archivos JSON
        archivos_json = [archivo for archivo in archivos if archivo.endswith('.json')]
        # Recorre los archivos y busca aquellos que terminen con ".json"
        # Lee y muestra el contenido de cada archivo JSON
        for archivo_json in archivos_json:
            with open(os.path.join(self.data_dir, archivo_json), 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    self.dl_course(data,archivo_json)
                except json.JSONDecodeError as e:
                    print(f'Error al decodificar {archivo_json}: {e}')
        # Mover cursos a la carpeta downloads
        for archivo_json in archivos_json:
            with open(os.path.join(self.data_dir, archivo_json), 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    move_folder(data['name'],'downloads')
                except json.JSONDecodeError as e:
                    print(f'Error al decodificar {archivo_json}: {e}')

clients = ['yt-dlp', 'aria2']
qualities = ['360', '480', '720', '1080', 'best']
help_d = 'Select the external downloader (yt-dlp or aria2). Default: yt-dlp. ' 
help_q = 'Select the video quality (360, 480, 720, 1080 or best). Default: best'

@click.command()
@click.option('-d', type=click.Choice(clients), default='yt-dlp', prompt=False, help=help_d)
@click.option('-q', type=click.Choice(qualities), default='best', prompt=False, help=help_q)
def main(d, q):
    check_aria2()
    # TODO: implement automatically get and save cookies
    dl = Downloader(external_downloader=d, quality=q)
    dl.bulk_download()

if __name__ == "__main__":
    main()
