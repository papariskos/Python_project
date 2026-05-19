import tkinter as tk
from gui.app import CourseApp


def main():
    root = tk.Tk()
    app = CourseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()