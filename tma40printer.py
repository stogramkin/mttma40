#!/usr/bin/env python3
import matplotlib
import tkinter as tk
import matplotlib.pyplot as plt
import numpy as np
from tkinter.filedialog import asksaveasfilename
import serial
#import sys
cmap = plt.get_cmap('Greys')


# Словарь всех hex символов группами по три
HexDec = dict()
for i in range(800):
    digit = hex(i)[2:].upper()
    if len(digit) == 1:
        digit = '00' + digit
    if len(digit) == 2:
        digit = '0' + digit
    HexDec[digit] = i
    


class App(tk.Frame):  
    def __init__(self, master):
        self.num1 = 10000 #это переменная, которая задает размеры массивов Y и сообщение. Она же - высота полотна
        tk.Frame.__init__(self, master)
       
        self.master = master
        self.DrawArea = tk.Canvas(self, width=600, height=self.num1, background="white",
                                  borderwidth=0, highlightthickness=0)
        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.DrawArea.xview)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.DrawArea.yview)
        self.DrawArea.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.DrawArea.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=2, sticky="ns")
        self.hsb.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.master.title('TMA 40 printer emulator')
# задаем размеры окна и максимум по вертикали и прикрепляем его к правой стороне
        window_params = '700x'+str(int(window.winfo_screenheight())-100)+'+' + str(int((window.winfo_screenwidth())-700)) + '+0'
        print(window.winfo_screenwidth())
        
        self.master.geometry(window_params)
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        file_items = tk.Menu(menubar)OD
        file_items.add_command(label='Сохранить', command=self.save_data)
        file_items.add_command(label='Выход', command=self.quit) #sys.exit)
        
        spectrum_items = tk.Menu(menubar)
        spectrum_items.add_command(label='Очистить экран', command=self.clear_screen)
        spectrum_items.add_command(label='Выбрать порт', command=self.choose_port)
        spectrum_items.add_command(label='Запустить измерения', command=self.start_exp)

        menubar.add_cascade(label='Файл', menu=file_items)
        menubar.add_cascade(label='Служебные', menu=spectrum_items)
        
        
        try:
            with open('port.conf', 'r') as port_log:
                self.serial_number = port_log.readline()
                
        except:
            self.serial_number = '/dev/ttyUSB0'
            with open('port.conf', 'w') as port_log:
                port_log.write(self.serial_number)
                self.thanks = False
        
        
    def quit(self): # Меню выхода из программы
        self.destroy()
        exit()
#    def closeapp(self):
#        self.destroy()
#        self.quit()

    def null_data(self, serial_number):
        self.ser = serial.Serial(port=serial_number, timeout=1, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, baudrate=9600)
        self.messages = np.zeros((self.num1, 3), dtype='object')
        self.to_print = np.zeros((700, self.num1), dtype=np.uint8)
        self.mode = 'text'
        self.mesnum = 0
        self.y = 0
        self.incr = 0
        
    
    def start_exp(self):
        self.null_data(self.serial_number)
        while True:
# сбрасываем в ноль счетчик строк при достиении значения 10000-50        
            if self.y > self.num1 - 50:
                self.y = 0
                self.DrawArea.delete("all")
                self.update()
            if self.mesnum > self.num1 -50:
                self.mesnum = 0
                self.messages = np.zeros((self.num1, 3), dtype='object')
                
            line = self.ser.readline()
            print (line)
            line_code = str(line)
            x1f_position = line_code.find('x1f')
            x1e_position = line_code.find('x1e')
            x0f_position = line_code.find('x0f')
            x0c_position = line_code.find('x0c')
            
        
            if x1f_position != -1 or x1e_position != -1:
                self.mode = 'text'
                line = line[max(x1e_position, x1f_position)-2:]
                
            
            if x0c_position != -1:
                self.y += 20
                self.mode = 'text'
                line = line[x0c_position-2:]
                
                try:
                    if self.thanks:
                        message = 'Спасибо, Рамиль! Это был отличный эксперимент! :3'
                        position = '000'

                        self.print_text(position, self.y, message)
                        self.y += 10
                        self.DrawArea.yview_moveto('1.0')
                        self.update()
                    self.thanks = False
                except: pass
 
            x1d_position = line_code.find('x1d')

            if x0f_position != -1:
                self.mode = 'data'
                self.thanks = True
                line = line[x0f_position - 2:] 
                x1d_position -= 4

            prev_message = ''
            
            if self.mode == 'text':
                message = line.decode('ascii')[:-2].replace('}', '\u00b0')
                if message.find('****') != -1: self.y += 20
                position = '000'
                self.messages[self.mesnum] = position, self.y, message
                self.mesnum += 1
                
                if message != prev_message:
                    self.print_text(position, self.y, message)
                    self.y += 10

                prev_message = message
                wrong_mode = ['P', 'S', 'A']
                
                if len(message) and message[0] in wrong_mode:
                    #print(message[0], ' ', type(message[0]))
                    self.mode = 'data'
                self.DrawArea.yview_moveto('1.0')
                self.update()

            elif self.mode == 'data':
                code = line.decode('utf8').strip()
                if len(code):
                    command = code[0]
                    if command == 'P':
                        begin = code[1:4]
                        end = code[4:]
                        if begin == end:
                            x = HexDec[begin]
                            self.to_print[x, self.y] = 1
                            self.incr += 1
                            self.draw(x, self.y)
                            self.DrawArea.yview_moveto('1.0')
                            self.update()

                        else:
                            x1 = HexDec[begin]
                            x2 = HexDec[end]
                            for x in range(x1, x2 + 1):
                                self.to_print[x, self.y] = 1
                                self.incr += 1
                                self.DrawArea.create_rectangle(x, self.y, x, self.y, fill='black')

                            self.DrawArea.configure(scrollregion = self.DrawArea.bbox("all"))
                            self.DrawArea.yview_moveto('1.0')
                            self.update()

                    elif command == 'A':
                        position = code[1:4]
                        message = str(code[x1d_position-2:]).replace('~m', '\u03BC'+'m')
                        self.messages[self.mesnum] = position, self.y, message
                        self.mesnum += 1
                        self.print_text(position, self.y, message)
                        self.DrawArea.yview_moveto('1.0')
                        self.update()

                    elif command=='S':
                        self.y += 1


    def draw(self, x, y):
        self.DrawArea.create_rectangle(x, y, x, y, fill='black')
        self.DrawArea.configure(scrollregion = self.DrawArea.bbox("all"))


    def print_text(self, position, y, message):
        self.DrawArea.create_text(int(HexDec[position]), int(y), anchor=tk.W, font='Arial 8', text=message)
        self.DrawArea.configure(scrollregion = self.DrawArea.bbox("all"))
       
        
    def clear_screen(self):
        self.ser.close()
        self.null_data(self.serial_number)
        self.DrawArea.delete("all")
        self.update()
        self.start_exp()
    
    
    def choose_port(self):
        self.child = tk.Toplevel(self.master)
        self.child.title('Выберите номер порта')
        self.child.geometry('80x130+{}+{}'.format(self.master.winfo_rootx()+110, self.master.winfo_rooty()-50))
        self.child.resizable(False, False)
        self.rvar = tk.StringVar()
        self.rvar.set(self.serial_number)
        tk.Radiobutton(self.child, text='/ttyUSB0', variable=self.rvar, value='/ttyUSB0', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)
        tk.Radiobutton(self.child, text='/ttyUSB1', variable=self.rvar, value='/ttyUSB1', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)
#        tk.Radiobutton(self.child, text='COM3', variable=self.rvar, value='COM3', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)
#        tk.Radiobutton(self.child, text='COM4', variable=self.rvar, value='COM4', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)
#        tk.Radiobutton(self.child, text='COM5', variable=self.rvar, value='COM5', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)
#        tk.Radiobutton(self.child, text='COM6', variable=self.rvar, value='COM6', indicator=0, width=80, command=self.port_setting).pack(anchor=tk.W)        
        
        self.child.mainloop()
    
    
    def port_setting(self):
        self.serial_number = self.rvar.get()
        with open('../port.txt', 'w') as port_log:
            port_log.write(self.serial_number)
        self.child.destroy()
        self.child.quit()
        
    
    def save_data(self):

        to_print = self.to_print[:, :self.y]
        autoscale = to_print.shape[1] / to_print.shape[0]
        messages = self.messages[self.messages[:, 2] != 0]
        
        a = asksaveasfilename(filetypes=(("TIF Image", "*.tif"),("All Files", "*.*")), 
            defaultextension='.tif', title="Сохранить")
        
        
        fig = plt.figure(figsize=(10, 10*autoscale), dpi=100)
        ax = fig.add_subplot(111)
        cmap = plt.get_cmap('Greys')

        ax.imshow(to_print.transpose(), cmap=cmap, interpolation=None, origin='upper', aspect=1)
        plt.axis('off')

        for item in messages:
            ax.text(int(HexDec[item[0]])-15, int(item[1])+3, item[2], size=8)
        fig1 = plt.gcf()
        if a:
            fig1.savefig(a, bbox_inches='tight')
            
        
window = tk.Tk()
App(window).pack(fill="both", expand=True)
window.mainloop()
