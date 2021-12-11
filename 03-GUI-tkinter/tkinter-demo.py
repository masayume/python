from tkinter import *

#
# use python3 <filename>
# 
# cfr. https://dev.to/anjalikumawat2002/gui-in-python-using-tkinter-gfa

def select():
    if choice.get()==1:
        order = "Large Pizza"
    elif choice.get()==2:
        order = "Medium Pizza"
    else:
        order = "Small Pizza"
    selection = "You have ordered "+order
    label.config(text=selection)

root = Tk()
root.title("Pizza Corner")
choice = IntVar()
rbLarge = Radiobutton(root, text = "Large Pizza",font=20,variable=choice,value=1,command=select)
rbMedium = Radiobutton(root, text = "Medium Pizza",font=20,variable=choice,value=2,command=select)
rbSmall = Radiobutton(root, text = "Small Pizza",font=20,variable=choice,value=3,command=select)
rbLarge.pack(anchor=W)
rbMedium.pack(anchor=W)
rbSmall.pack(anchor=W)
label = Label(root,text="Choose pizza that you want!!",font=35)
label.pack()
mainloop()
