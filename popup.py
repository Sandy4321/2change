import os
import Tkinter, tkMessageBox

def main():
    # load 'qualifying' number of sessions so far
    sessionFile = 'data/num_sessions.txt'

    if os.path.exists(sessionFile):
        with open(sessionFile) as sfl:
            content = sfl.readlines()
            phase = content[0].strip()
            sessionNum = int(content[1])
    else:   
        phase = 'PreTraining'
        sessionNum = 0

    if 'Training' in phase: critSessionNum = 2
    else:                   critSessionNum = 40

    if sessionNum >= critSessionNum:
        root = Tkinter.Tk()
        root.withdraw()
        tkMessageBox.showinfo(phase + ' phase finished!', phase + ' phase finished!\nPlease let Jesse know. \n\nThank you! ')
        root.destroy()

if __name__ == '__main__':
    main()