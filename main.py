import tkinter as tk
from sys import argv
if len(argv)>1:
    if argv[1]=="dev":
        from gui_new import TransactionApp
else:
    from gui import TransactionApp

def main():
    root = tk.Tk()
    app = TransactionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
