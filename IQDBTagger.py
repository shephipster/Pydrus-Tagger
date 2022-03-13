import threading
import tkinter as tk
from tkinter import ttk
from Hydrus.ProcessedFilesIO import ProcessedFilesIO
import Hydrus.HydrusApi as HydrusApi
import Services.IQDBService as IQDB
import time
from threading import Thread

fio = ProcessedFilesIO("./tempFiles/processedIQDBHashes.txt")

debug = False

#GUI
class App(tk.Tk): 
    def __init__(self):
        super().__init__()

        self.title("PyQDB Tagger")
        self.resizable(0,0)

        self.state = 0  #Uninitialized | initialized | running | paused | stopping
        self.iter = 0   #number of files processed
        self.fileId = -1
        self.timerTotal = 0
        self.timerOne = 0
        self.timerTwo = 0
        self.totalFiles = 0
        self.hashesToProcess = []
        self.totalFilesDone = 0
        self.newFiles = 0

        self.lastFile = ""

        self.create_display_frame()
        self.create_button_frame()
        self.create_input_frame()

    def create_input_frame(self):
        self.inputFrame = ttk.Frame(self)

        # self.pauseLabel = ttk.Label(self.inputFrame, text='Pause Limit')
        # self.pauseLabel.grid(column=0, row=0)
        # self.pauseAfterVar = tk.StringVar()
        # self.pauseAfterInput = ttk.Entry(self.inputFrame, textvariable=self.pauseAfterVar, width=4)
        # self.pauseAfterInput.grid(column=1, row=0)

        self.stopLabel = ttk.Label(self.inputFrame, text="Stop Limit")
        self.stopLabel.grid(column=0, row=0)
        self.stopAfterVar = tk.StringVar()
        self.stopAfterInput = ttk.Entry(self.inputFrame, textvariable=self.stopAfterVar, width=4)
        self.stopAfterInput.grid(column=1, row=0)
        self.stopAfterInput.insert(0,"100")

        self.inputFrame.grid(column=0, row=1, padx=0, pady=0)

    def create_button_frame(self):
        self.buttonFrame = ttk.Frame(self)

        self.buttonFrame.columnconfigure(0, weight=1)
        self.buttonFrame.columnconfigure(1, weight=1)
        self.buttonFrame.columnconfigure(2, weight=1)
        self.buttonFrame.columnconfigure(3, weight=1)

        self.init_button = tk.Button(self.buttonFrame, bg="Blue", activebackground="Dark Blue", text="Initialize", width=6, height=4, command=self.initialize)
        self.init_button.grid(row=0, column=0)

        self.resume_button = tk.Button(self.buttonFrame, bg="Green", activebackground="Dark Green", text="Run", width=6, height=4, command=self.run)
        self.resume_button.grid(row=0, column=1)
        self.resume_button['state'] = tk.DISABLED

        self.pause_button = tk.Button(self.buttonFrame, bg="Red", activebackground="Dark Red", text="Pause", width=6, height=4, command=self.pause)
        self.pause_button.grid(row=0, column=2)
        self.pause_button['state'] = tk.DISABLED

        self.end_button = tk.Button(self.buttonFrame, bg="Yellow", activebackground="Dark Green", text="Stop", width=6, height=4, command=self.terminate)
        self.end_button.grid(row=0, column=3)
        self.end_button['state'] = tk.DISABLED

        self.buttonFrame.grid(column=0, row=2, sticky=tk.NSEW, padx=0, pady=5)

    def create_display_frame(self):
        self.displayFrame = ttk.Frame(self)

        self.displayFrame.rowconfigure(0, weight=1)
        self.displayFrame.rowconfigure(1, weight=1)
        self.displayFrame.rowconfigure(2, weight=1)

        self.statusDisplay = tk.Label(self.displayFrame, height=1, width=50, textvariable="")
        self.statusDisplay.config(text="Status: Needs Initialization. Press \"Initialize\"")
        self.statusDisplay.grid(row=0)

        self.stageDisplay = tk.Label(self.displayFrame, height=1, width=50, textvariable="")
        self.stageDisplay.config(text=f"Files Processed: 0")
        self.stageDisplay.grid(row=1)

        self.timeDisplay = tk.Label(self.displayFrame, height=1, width=50, textvariable="")
        self.timeDisplay.config(text="Elapsed Time: 00:00:00")
        self.timeDisplay.grid(row=2)

        self.displayFrame.grid(column=0, row=0, sticky=tk.NSEW, padx=0, pady=0)

    def initialize(self):
        if(self.state == 0):
            self.init_button['state'] = tk.DISABLED
            self.pause_button['state'] = tk.NORMAL
            initializeThread = FileFinder()
            initializeThread.start()
            self.timerOne = time.time()
            self.statusDisplay.config(text="Status: Finding new files...")

            self.monitorInit(initializeThread)

    def run(self):
        if(self.state == 1 or self.state == 3):
            self.resume_button['state'] = tk.DISABLED
            self.pause_button['state'] = tk.NORMAL
            self.end_button['state'] = tk.DISABLED
            self.state = 2
            self.statusDisplay.config(text="Status: Processing files...")
            #resume the timer
            self.timerOne = time.time()
            processThread = Processor(self.hashesToProcess)
            processThread.start()
            self.monitorProcess(processThread)
            self.stopAfterInput['state'] = tk.DISABLED

    def pause(self):
        if(self.state == 2):
            self.resume_button['state'] = tk.NORMAL
            self.end_button['state'] = tk.NORMAL
            self.pause_button['state'] = tk.DISABLED
            self.state = 3
        #TODO: Allow pausing of the initial file loading

    def terminate(self):
        #save any progress first, then exit out
        #TODO: Save
        self.destroy()

    def monitorProcess(self, thread):
        if self.state == 3: #paused
            self.statusDisplay.config(text="Status: Pausing...")
            thread.stop()

        if (self.totalFilesDone == self.newFiles) or (self.totalFilesDone != 0 and self.totalFilesDone == int(self.stopAfterVar.get())):
            thread.stop()
            self.statusDisplay.config(text="Status: Processing done, feel free to stop")
            while thread.is_alive():
                time.sleep(1)
            self.state = 5
            self.resume_button['state'] = tk.DISABLED
            self.pause_button['state'] = tk.DISABLED
            self.end_button['state'] = tk.NORMAL
            self.after(100, lambda: self.awaitEnd())
        # if self.totalFilesDone != 0 and self.totalFilesDone % int(self.pauseAfterVar.get()) == 0:
        #     self.state == 3
        
        #for now, just run the timer
        if thread.is_alive():
            if thread.count != 0 and len(thread.handledFiles) != 0 and self.lastFile != thread.mostRecent:
                self.totalFilesDone += 1
                self.lastFile = thread.mostRecent
            self.timerTwo = time.time()
            duration = self.timerTwo - self.timerOne
            self.timerOne = self.timerTwo
            self.timerTotal += duration
            hours, rem = divmod(self.timerTotal, 3600)
            mins, secs = divmod(rem, 60)
            self.timeDisplay.config(text="Elapsed Time: %02d:%02d:%02d" % (hours, mins, secs))
            self.stageDisplay.config(text="Files Processed: %d/%d" % (self.totalFilesDone, min(int(self.stopAfterVar.get()), self.newFiles)))
            self.after(100, lambda: self.monitorProcess(thread))            
        else:
            if self.state != 5:
                self.statusDisplay.config(text="Status: Paused")

    def monitorInit(self, thread):
        if thread.is_alive():
            self.timerTwo = time.time()
            duration = self.timerTwo - self.timerOne
            self.timerOne = self.timerTwo
            self.timerTotal += duration
            hours, rem = divmod(self.timerTotal, 3600)
            mins, secs = divmod(rem, 60)
            self.timeDisplay.config(text="Elapsed Time: %02d:%02d:%02d" % (hours, mins, secs))
            self.statusDisplay.config(text="Status: Found %d new files (%d total)" % (len(thread.newFiles), thread.numFiles))
            self.after(100, lambda: self.monitorInit(thread))
        else:           
            if(len(thread.newFiles) == 0):
                #there was no new file
                self.statusDisplay.config(text="Status: No new file was found!")
                self.end_button['state'] = tk.NORMAL
            else:
                self.resume_button['state'] = tk.NORMAL
                self.end_button['state'] = tk.NORMAL
                self.pause_button['state'] = tk.DISABLED
                self.hashesToProcess = thread.newFiles
                self.totalFiles = thread.numFiles
                self.newFiles = len(thread.newFiles)
                self.statusDisplay.config(text="Status: %d files found, %d new. Ready to process" % (self.totalFiles, self.newFiles))
            self.state = 1

    def awaitEnd(self):
        if self.state == 5:
            #just waiting on user to hit stop
            self.after(100, lambda: self.awaitEnd())

#Only job is to find the first file to process
class FileFinder(Thread):

    def __init__(self):
        super().__init__()
        self.numFiles = 0
        self.newFiles = []

    def run(self):
        #for all files
        #Why in the world was I using the id and making more calls for the hash?
        fileData = HydrusApi.getAllMainFileData()
        for key in fileData.keys():
            self.numFiles += 1
            if not fio.hashInFile(fileData[key]['hash']):
                if isValidFile(fileData[key]):
                    self.newFiles.append(fileData[key]['hash'])
                else:
                    fio.addHash(fileData[key]['hash'])
        fio.save()


#Handles the actual processing of the files and tagging them
class Processor(Thread):

    def __init__(self, files):
        super().__init__()
        self._stop_event = threading.Event()
        self.count = 0
        self.filesToHandle = files
        self.handledFiles = []
        self.mostRecent = ""

    #this is called a lot, need to figure out why. Already confirmed that there's only ever 2 threads
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
  
    def run(self):
        #Process file one at a time, pausing briefly between them to avoid API limits
        while(not self.stopped()):
            fileHash = self.filesToHandle[0]
            try:
                if isValidFile(HydrusApi.getMetaFromHash(fileHash)):
                    image = HydrusApi.getImageByHash(fileHash)
                    data = IQDB.getAllInfoFromFile(image)
                    if not data == None:  
                        self.processFile(data, fileHash)
                else:
                    print(f"Invalid file, hash {fileHash}")
            except Exception as e:
                 print("Exception:", e)
                 print("Failed hash:", fileHash)
                 return
            finally:
                fio.addHash(fileHash)
                self.filesToHandle.remove(fileHash)            
                self.count += 1
                self.handledFiles.append(fileHash)
                self.mostRecent = fileHash
                fio.save()
                #help prevent reaching api limits
                time.sleep(5) 
                if self.count % 50 == 0:
                    time.sleep(25)
        self.join()

    def processFile(self, data, hash):
        tags = data['tags']
        urls = data['urls']
        for url in urls:
            HydrusApi.addKnownURLToFileByHash(hash, url)
            HydrusApi.uploadURL(url)
        for tag in tags:
            HydrusApi.addTagByHash(hash, tag)



def isValidFile(fileMeta):
    if fileMeta['size'] > IQDB.FILE_LIMIT:
        #print(f"{fileMeta['hash']} too large for IQDB")
        return False

    if fileMeta['mime'] not in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
        #print(f"{fileMeta['hash']} not a valid file type")
        return False

    return True

app = App()
app.mainloop()