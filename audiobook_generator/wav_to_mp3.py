import os




def wav_to_mp3(input_file, output_file):
    cmd = f"ffmpeg -i {input_file} -vn -ar 44100 -ac 2 -b:a 192k {output_file}"
    os.system(cmd)
