#!/usr/bin/python

import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image
from glob import glob
from itertools import cycle
import cv2
import numpy as np
import os 
import shutil
from tkinter import filedialog as fd
from tkinter import simpledialog as sd
from tkinter.messagebox import showinfo
from train_test_txts import get_extracted_txts
import uuid


class Window:
    def __init__(self,success="success",fail="fail",initial_dir='./D-Fire'): # 
        self.img_pos = 0
        self.mask_track=0
        self.images = []
        self.annotations = []
        self.fail_dir = fail
        self.success_dir = success
        self.root = tk.Tk()
        self.img_pad = 5
        self.label_pad = 2
        self.initial_dir = initial_dir
        self.txt_dir = None
        self.selected_dataset = None
        self.current_image = None
        self.alpha_var = tk.DoubleVar()
        self.alpha_var.set(0.6)
        self.blur_var = tk.IntVar()
        self.blur_var.set(1)
        self.slider_pad = 3

        #menu items
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.dataset_menu = tk.Menu(self.menu)
        self.dataset_menu.add_command(label="Open",command=self.select_dir)
        self.dataset_menu.add_command(label="Generate",command=self.generate_dataset_txt)
        self.dataset_menu.add_command(label="Save As...",command=self.regenerate_dataset_txt)
        self.menu.add_cascade(label="File",menu=self.dataset_menu)


        self.buttons_frame = tk.Frame(self.root)
        self.generate_dataset_txt_button = tk.Button(self.buttons_frame,text='Generate Dataset txt',command=self.generate_dataset_txt)
        self.generate_dataset_txt_button.grid(row=0,column=0)
        self.open_dataset_button = tk.Button(self.buttons_frame,text='Open Dataset txt',command=self.select_dir)
        self.open_dataset_button.grid(row=0,column=1)
        self.regenerate_txts_button = tk.Button(self.buttons_frame,text='Save As...',command=self.regenerate_dataset_txt)
        self.regenerate_txts_button.grid(row=0,column=2)
        self.list_count_label = tk.Label(self.buttons_frame,text ='List Count: '+str(len(self.images)))
        self.list_count_label.grid(row=0,column=3)
        self.buttons_frame.pack(side=TOP,pady=self.label_pad)
        
        #canvas
        self.canvas_frame = tk.Frame(self.root)
        self.canvas = tk.Label(self.canvas_frame)
        self.canvas.grid(row=0,column=0,padx=self.img_pad,pady=self.img_pad)
        self.original = tk.Label(self.canvas_frame)
        self.original.grid(row=0,column=1,padx=self.img_pad,pady=self.img_pad)
        self.canvas_frame.pack()

        #sliders
        self.slider_frame = tk.Frame(self.root)
        self.slider_label = tk.Label(self.slider_frame,text = 'Alpha')
        self.slider_label.grid(row=0,column=0,padx=self.label_pad,pady=self.label_pad)
        self.slider =  tk.Scale(self.slider_frame,from_=0.0,to=1.00,resolution=0.1,orient=tk.HORIZONTAL,variable=self.alpha_var,command=self.mask_overlay)
        self.slider.grid(row=0,column=1,padx=50)
        self.slider_blur =  tk.Scale(self.slider_frame,from_=1,to=27,resolution=2,orient=tk.HORIZONTAL,variable=self.blur_var,command = self.mask_overlay)
        self.slider_blur.grid(row=0,column=2,pady=self.label_pad)
        self.slider_label_blur = tk.Label(self.slider_frame,text = 'Blur Kernel Size')
        self.slider_label_blur.grid(row=0,column=3,padx=self.label_pad)
        self.slider_frame.pack(side=BOTTOM)

        #window_config
        self.root.bind('<Left>',self.leftKey)
        self.root.bind('<Right>',self.rightKey)
        self.root.bind('<Down>',self.down)
        self.root.bind('<Up>',self.up)
        self.root.bind('<Escape>',self.escape)
        self.root.winfo_toplevel().title("CleanUI")
        
        self.root.geometry("640x480")
        self.root.mainloop()


    def regenerate_dataset_txt(self):
        if self.selected_dataset is None:
            return
        image = self.selected_dataset.split('\t')[0]
        image_dir = os.path.dirname(self.selected_dataset.split('\t')[0])
        annot_dir = os.path.dirname(self.selected_dataset.split('\t')[1])
        image_ext = '.'+image.split('.')[-1]
        f = fd.askopenfile(mode='r',title='Save', filetypes =[('Text Files', '*.txt')],initialdir=self.initial_dir)
        if not f:
            return
        filename = f.name 
        f.close()
        get_extracted_txts(image_dir,annot_dir,image_ext,filename)
        self.load_data(filename)


    def generate_dataset_txt(self):
        self.images.clear()
        self.annotations.clear()
        image_dir = fd.askdirectory(title="Select Image Directory",initialdir=self.initial_dir)
        if not image_dir:
            return
        parent_dir = os.path.abspath(os.path.join(image_dir, os.pardir))
        annot_dir = fd.askdirectory(title="Select Annotations Directory",initialdir=parent_dir)
        if not annot_dir:
            return
        image_ext = sd.askstring(title="Set image extension",prompt='Enter image extension',initialvalue='.jpg')
        if not image_ext:
            return
        lists_dir = os.path.join(os.path.abspath(self.initial_dir),'lists')

        if not os.path.exists(lists_dir):
            os.mkdir(lists_dir)
        filename = os.path.join(lists_dir,str(uuid.uuid4())+'.txt')
        get_extracted_txts(image_dir,annot_dir,image_ext,filename)
        self.load_data(filename)


    def load_data(self,filename):
        self.txt_dir = filename
        f = open(filename,'r')
        lines = f.readlines()
        self.selected_dataset  = lines[0]
        f.close()
        self.images = [i.split('\t')[0] for i in lines]
        self.annotations = [i.split('\t')[1].rstrip() for i in lines]
        h,w = self.mask_overlay()
        self.set_frame_size(h,w)

    def select_dir(self):
        self.images.clear()
        self.annotations.clear()
        f = fd.askopenfile(mode='r',title='Select Txt', filetypes =[('Text Files', '*.txt')],initialdir=self.initial_dir)
        if not f:
            return
        f.close()
        self.load_data(f.name)
        
    def mask_overlay(self,event=None):
        if len(self.images) == 0:
            return
        im = self.images[self.img_pos]
        self.current_image =im
        annot = self.annotations[self.img_pos]
        image = cv2.resize(cv2.imread(im),(640,480))
        copy = cv2.resize(cv2.imread(im),(640,480))
        if os.path.exists(annot):
            temp = cv2.resize(cv2.imread(im),(640,480))
            mask =  cv2.resize(cv2.imread(annot,cv2.IMREAD_GRAYSCALE),(640,480))
            mask = cv2.GaussianBlur(mask,(self.blur_var.get(),self.blur_var.get()),0)
            temp[mask>0,:] = [238,45,28]
            cv2.addWeighted(image,self.alpha_var.get(),temp,1-self.alpha_var.get(),0.0,image)
        
        img_pil = Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
        img_pil_orig = Image.fromarray(cv2.cvtColor(copy,cv2.COLOR_BGR2RGB))
        self.img = ImageTk.PhotoImage(image=img_pil)
        self.orig = ImageTk.PhotoImage(image=img_pil_orig)
        self.canvas.config(image=self.img)
        self.original.config(image=self.orig)
        title = self.images[self.img_pos].split('/')[-1]
        self.root.winfo_toplevel().title(title)
        self.list_count_label.configure(text='List Count: '+str(len(self.images)))
        return image.shape[:2]

    def down(self,event):
        image_to_move = self.images[self.img_pos]
        if self.current_image != image_to_move:
            return
        annotation_to_move = self.annotations[self.img_pos]
        img_dir = os.path.join(os.path.dirname(image_to_move),self.fail_dir)
        label_dir = os.path.join(os.path.dirname(annotation_to_move),self.fail_dir)

        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        if os.path.exists(image_to_move):
            shutil.move(image_to_move,img_dir)
            self.images.remove(image_to_move)

        if not os.path.exists(label_dir):
            os.mkdir(label_dir)

        if os.path.exists(annotation_to_move):
            shutil.move(annotation_to_move,label_dir)
            self.annotations.remove(annotation_to_move)

    
    def up(self,event):
        image_to_move = self.images[self.img_pos]
        if self.current_image != image_to_move:
            return
        annotation_to_move = self.annotations[self.img_pos]
        img_dir = os.path.join(os.path.dirname(image_to_move),self.success_dir)
        label_dir = os.path.join(os.path.dirname(annotation_to_move),self.success_dir)

        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        if os.path.exists(image_to_move):
            shutil.move(image_to_move,img_dir)
            self.images.remove(image_to_move)

        if not os.path.exists(label_dir):
            os.mkdir(label_dir)

        if os.path.exists(annotation_to_move):
            image = cv2.imread(annotation_to_move,cv2.IMREAD_GRAYSCALE)
            if self.blur_var.get() != 1:
                image = cv2.GaussianBlur(image,(self.blur_var.get(),self.blur_var.get()),0)
            cv2.imwrite(annotation_to_move.split('.')[0]+".png",image)
            shutil.move(annotation_to_move,label_dir)
            self.annotations.remove(annotation_to_move)


    def set_frame_size(self,h,w):
        w *= 2 
        h += 2*(self.img_pad+self.label_pad+self.slider_pad)+self.open_dataset_button.winfo_height()+self.slider_frame.winfo_height()
        w += 2*self.img_pad
        d = f"{w}x{h}".format("%dx%d")
        self.root.geometry(d)

    def leftKey(self,event):
        self.img_pos-=1
        if self.img_pos<0:
            self.img_pos=len(self.images)-1
        self.mask_overlay()

    def rightKey(self,event):
        self.img_pos+=1
        if self.img_pos>=len(self.images):
            self.img_pos=0
        self.mask_overlay()

    def escape(self,event):
        self.root.quit()


Window()

#Window()