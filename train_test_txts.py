import os 

def get_extracted_txts(image_dir,annotations_dir,image_ext,filename):
    f = open(filename, 'w')

    dire= sorted(os.listdir(annotations_dir))
    for i in dire:
        im = os.path.join(image_dir,i.split('/')[-1].split('.')[0]+image_ext)
        annot = os.path.join(annotations_dir,i)
        if annot.endswith('.jpg'):
            f.write(im+'\t'+annot+'\n')
    f.close()


def extract_txt(path:str, filename:str,image_dir:str,image_ext:str,annotations_dir:str):
    now = os.getcwd()
    f = open(os.path.join(now,path,'lists',filename+'.txt'), 'w')
    dire= os.listdir(os.path.join(now,path, filename,annotations_dir))
    for i in dire:
        im = os.path.join(now,path,filename,image_dir,i.split('/')[-1].split('.')[0]+image_ext)
        annot = os.path.join(now,path,filename,annotations_dir,i)
        if annot.endswith('.jpg'):
            f.write(im+'\t'+annot+'\n')
    f.close()
