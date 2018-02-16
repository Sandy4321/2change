#!/usr/bin/env python

#   ___     _____ _                            
#  |__ \   / ____| |                           
#     ) | | |    | |__   __ _ _ __   __ _  ___ 
#    / /  | |    | '_ \ / _` | '_ \ / _` |/ _ \
#   / /_  | |____| | | | (_| | | | | (_| |  __/
#  |____|  \_____|_| |_|\__,_|_| |_|\__, |\___|
#                                    __/ |     
#                                   |___/                                      

from __future__ import division
from itertools import groupby
import sys
sys.path.append('c:/')
sys.path.append('..')
from lrc import *

# open file for error log
sys.stderr = open('errorlog.txt', 'w')

# HELPER CLASSES
def runsTooLong(l):
    """
    Gets run lengths of a list. Returns vector of booleans indicating 
    whether runs are 3+ long.
    """
    return [len(list(group)) > 3 for name, group in groupby(l)]

def pseudoRandomizeIsChangedList():
    """Shuffle isChangedList until no runs are longer than 3."""
    global isChangedList
    x = [item[0] for item in isChangedList]

    while any(runsTooLong(x)):
        random.shuffle(isChangedList)
        x = [item[0] for item in isChangedList]

def delay(milliseconds):
    """
    Wait for a number of milliseconds. Still allows to quit out of 
    programme.
    """
    elapsed = 0
    while elapsed < milliseconds/1000:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_q):
                if file:    writeLn(file)
                pygame.quit()
                sys.exit()
            if event.type == TICK:
                elapsed += 1

class Image(Box):
    """Load image #`index` from `files` list and center it at (400, 150). """
    def __init__(self, index, version = 0):
        super(Image, self).__init__()

        if type(files[index]) is str:   self.folder = int(files[index][5:6])
        else:                           self.folder = int(files[index][0][5:6])

        # load image depending on folder
        # if phase3/4 (test2/3), then load correct version. version 0 = original
        if self.folder <= 2: self.image = pygame.image.load(files[index]).convert_alpha()
        else:                self.image = pygame.image.load(files[index][version]).convert_alpha()

        # scale image depending on folder
        if self.folder == 2:
            self.image = pygame.transform.smoothscale(self.image, (233, 200))
        elif self.folder == 3:
            self.image = pygame.transform.smoothscale(self.image, (300, 300))
        elif self.folder == 4:
            self.image = pygame.transform.smoothscale(self.image, (400, 300))

        # if checkerboard, offset from the middle so it appears in the middle
        self.rect = self.image.get_rect()
        if self.folder == 4:   self.rect.center = self.pos = (435, 175)
        else:                  self.rect.center = self.pos = (400, 175)

        if self.folder <=2:  self.name = files[index][15:-4]
        else:                self.name = files[index][version][15:-4]

class Button(Box):
    """Button icons for the correct and incorrect icons."""
    def __init__(self, file, pos):
        super(Button, self).__init__()
        image = pygame.image.load(file).convert_alpha()
        self.size = image.get_size()
        scaled = (int(1 * self.size[0]), int(1 * self.size[1]))
        self.image = pygame.transform.smoothscale(image, scaled)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos = pos
        self.mask = pygame.mask.from_surface(self.image)

class Trial(object):
    """Initialise trial with properties set to 0 or empty. """
    def __init__(self, phase):
        self.phase = phase
        if self.phase == 'PreTraining':    self.block = 0
        else:                              self.block = sessionNum
        self.number = 0
        self.numCorrect = 0
        self.stimuli = []
        self.isChanged = None
        self.sampleIsOccluded = 'NA'
        self.wasCorrect = None
        self.t0 = 0
        self.RT = 0
        self.isStartScreen = None
        self.idx = 0

    def new(self):
        """
        Determine block and trial number. Set `screen` to 'Start' to present 
        start box. Set trial parameters. Make stimuli and reset cursor.
        """
        if self.number % BLOCK_LENGTH == 0:
            self.newBlock()

        if phase == 'PreTraining' and self.number % 6 == 0:
            random.shuffle(files)

        self.number += 1
        self.isStartScreen = True
        self.isChanged = isChangedList[self.number - 1][0]
        if phase == 'Test2':
            self.sampleIsOccluded = isChangedList[self.number - 1][1]

        if 'Training' in phase: self.params = [TRAINING_DURATION_SEARCH_DISPLAY, 0]
        else:                   self.params = paramList[self.number - 1]

        self.makeStimuli()
        cursor.mv2pos((400, 350))

    def repeat(self):
        """
        Repeat trial with different stimuli but same parameters otherwise. 
        Set `screen` to 'Start' to present start box. Make stimuli and 
        reset cursor.
        """
        self.isStartScreen = True

        self.makeStimuli(True)
        cursor.mv2pos((400, 350))

    def newBlock(self):
        """
        Overwrite `data/num_sessions.txt` with finished session number 
        (for training phase only if 80% criterion met in *last* block). Adjust if
        it was already incremented 'today'. Increment block counter, reset 
        trial and numCorrect counts, and pseudo-randomize params for next block.
        """

        # if at least one block of test condition/s completed, increment `num_sessions.txt`
        if 'Test' in phase and self.block > 0:
            with open(sessionFile, 'w') as sfl:
                sfl.write(phase + '\n' + str(self.block))

        if 'Training' in phase and self.block > 0:
            with open(lastRun, 'w') as sfl:       sfl.write(today)

            # if current completed training block met criterion, increment `num_sessions.txt`
            if self.numCorrect >= .8*BLOCK_LENGTH:
                with open(sessionFile, 'w') as sfl:
                    if lastDate == today:   sfl.write(phase + '\n' + str(sessionNum))
                    else:                   sfl.write(phase + '\n' + str(sessionNum + 1))

            # if current completed training block didn't meet criterion, reset `num_sessions.txt`
            else:
                with open(sessionFile, 'w') as sfl:
                    if lastDate == today:   sfl.write(phase + '\n' + str(sessionNum - 1))
                    else:                   sfl.write(phase + '\n' + str(sessionNum))

        if ('Test' in self.phase) and (self.block >= NUM_TEST_SESSIONS):
            pygame.quit()
            sys.exit()

        self.block += 1
        self.number = 0
        self.numCorrect = 0
        pseudoRandomizeIsChangedList()
        random.shuffle(paramList)
        random.shuffle(files)

    def makeStimuli(self, repeat = False):
        """
        Pick new sample from randomized file list (makes it non-repeating 
        within this block). Except, if this trial is repeated, then pick a 
        random sample (that is not one presented right before) so images can't 
        get depleted. If sample is supposed to change, then pick another,
        different image.
        """
        if repeat:  self.idx = random.choice(range(0, self.idx) + range(self.idx + 1, len(files)))
        else:       self.idx = self.number - 1

        if phase == 'PreTraining':
            self.idx %= 6

        # if Test2 (phase3), then sample is either the occluded one or the original one
        # in all other phases, the sample is the original/only pic
        if self.phase == 'Test2':   self.stimuli = [Image(self.idx, self.sampleIsOccluded)]
        else:                       self.stimuli = [Image(self.idx)]

        if self.isChanged:
            if self.phase == 'Test2':
                # changed image is occluded (if sample is original) or the original (if sample is occluded)
                self.stimuli += [Image(self.idx, 1-self.sampleIsOccluded)]
            elif self.phase == 'Test3':
                # changed image is drawn from folder that corresponds to block
                self.stimuli += [Image(self.idx, (self.block - 1) % 5 + 1)]
            elif self.phase == 'Test4':
                # changed image is drawn from folder that corresponds to block
                self.stimuli += [Image(self.idx, (self.block - 1) % 3 + 1)]
            # Training/Test1
            else:
                lst = range(0, self.idx) + range(self.idx + 1, len(files))
                self.stimuli += [Image(random.choice(lst))]

    def start(self):
        """Draw startbox, show sample upon collision."""
        mvCursor(cursor, only = 'up')

        startbox.draw(bg)
        bg.blit(starttext, startpos)
        cursor.draw(bg)

        if cursor.pxCollide(startbox):
            bg.fill(Color('white'))
            refresh(screen)
            cursor.mv2pos((400, 450))

            # show sample
            self.stimuli[0].draw(bg)
            refresh(screen)
            delay(self.params[0])

            # show blank flicker
            bg.fill(Color('white'))
            refresh(screen)
            delay(self.params[1])

            # show test screen, start measuring RT
            self.isStartScreen = False
            self.t0 = pygame.time.get_ticks()

    def test(self):
        """
        Display test image. If time out (after 5s), repeat trial. If selection, 
        whoop + pellet (if correct) or buzz + timeout (if incorrect).
        """
        self.stimuli[self.isChanged].draw(bg)

        mvCursor(cursor, only = 'right, left')
        cursor.draw(bg)

        select = cursor.collide(buttons)
        for b in buttons:   b.draw(bg)

        self.RT = pygame.time.get_ticks() - self.t0

        # timeout after 5s --> repeat trial
        if self.RT >= RESPONSE_WINDOW:
            self.RT = RESPONSE_WINDOW
            self.wasCorrect = 'NA'
            self.write(file)
            self.repeat()

        # before that, if a choice was made
        elif select > -1:
            self.wasCorrect = int(select != self.isChanged)
            self.write(file)
            sound(self.wasCorrect)

            if self.wasCorrect:
                self.numCorrect += 1
                pellet()
            else:
                bg.fill(Color('grey'))
                refresh(screen)
                delay(TIMEOUT)
            self.new()

    def write(self, file):
        """Write data to file."""
        now = time.strftime('%H:%M:%S')
        if self.isChanged:  names = [s.name for s in self.stimuli]
        else:               names = [self.stimuli[0].name]*2

        data = [monkey, today, now, phase, self.block, self.number, self.isChanged, self.sampleIsOccluded] + names + self.params + [self.RT, self.wasCorrect]
        writeLn(file, data)
        # print data

# SETUP
# load (completed) session number from previous session
# and check if it was incremented 'today'
sessionFile = 'data/num_sessions.txt'
lastRun = 'data/last_completed.txt'

if os.path.exists(sessionFile):
    with open(sessionFile) as sfl:
        content = sfl.readlines()
        phase = content[0].strip()
        sessionNum = int(content[1])
else:   
    phase = 'PreTraining'
    sessionNum = 0

if os.path.exists(lastRun):
    with open(lastRun) as lfl:
        lastDate = lfl.read()
else:
    lastDate = ''

# set parameters
BLOCK_LENGTH = 120
REPS = 4
TRAINING_DURATION_SEARCH_DISPLAY = 1000
DURATION_SEARCH_DISPLAY = [250, 500, 1000, 2500, 5000]
DURATION_MASK = [0, 50, 100, 250, 500, 1000]
RESPONSE_WINDOW = 5000
TIMEOUT = 20000
NUM_TEST_SESSIONS = 40

# check whether number of sessions was reached previously
if 'Training' in phase: critSessionNum = 2
else:                   critSessionNum = NUM_TEST_SESSIONS

if sessionNum >= critSessionNum:
    pygame.quit()
    sys.exit()

# make data file w/ header
if not os.path.exists('data'):
    os.makedirs('data')

file = 'data/' + makeFileName('2change')
header = ['monkey', 'date', 'time', 'phase', 'block', 'trial', 'isChanged?', 'sampleIsOccluded?', 'search_img', 'test_img', 'dur_search', 'dur_flicker', 'RT', 'wasCorrect?']
writeLn(file, header)
# print header


# set screen; define cursor
screen = setScreen()
cursor = Box(circle = True)

# define start box
startbox = Box(col = Color('grey75'), pos = (400, 175), size = (150, 80))
font = pygame.font.SysFont('Arial', 14)
starttext = font.render('Start', 1, Color('black'))
startpos = starttext.get_rect(centerx = 400, centery = 175)

# define buttons
buttons = [Button('change.png', (200, 450)), Button('nochange.png', (600, 450))]

# create list of changed/isn't changed
isChangedList = zip(BLOCK_LENGTH//2 * [0] + BLOCK_LENGTH//2 * [1], BLOCK_LENGTH//2 * [0, 1])

# create list of delays for a block (for pseudo-randomisation)
paramList = []

if 'Test' in phase:
    for r in range(REPS):
        for d_search in DURATION_SEARCH_DISPLAY:
            for d_mask in DURATION_MASK:
                paramList.append([d_search, d_mask])

# load file list
if phase == 'Training':       files = glob.glob('phase1_stimuli/*.gif')
elif phase == 'PreTraining':  files = glob.glob('phase0_stimuli/*.gif')
elif phase == 'Test1':        files = glob.glob('phase2_stimuli/*.bmp')
elif phase == 'Test2':
    files = zip(glob.glob('phase3_stimuli/original/*.GIF'), 
                glob.glob('phase3_stimuli/occluded/*.GIF'))
elif phase == 'Test3':
    files = zip(glob.glob('phase4_stimuli/original/*.jpg'),
                glob.glob('phase4_stimuli/changed1/*.jpg'),
                glob.glob('phase4_stimuli/changed2/*.jpg'),
                glob.glob('phase4_stimuli/changed3/*.jpg'),
                glob.glob('phase4_stimuli/changed4/*.jpg'),
                glob.glob('phase4_stimuli/changed5/*.jpg'))
elif phase == 'Test4':
    files = zip(glob.glob('phase5_stimuli/original/*.jpg'),
                glob.glob('phase5_stimuli/changed1/*.jpg'),
                glob.glob('phase5_stimuli/changed2/*.jpg'),
                glob.glob('phase5_stimuli/changed3/*.jpg'))

# start clock
clock = pygame.time.Clock()
TICK = USEREVENT + 1
pygame.time.set_timer(TICK, 1000)


# MAIN GAME LOOP: start first trial
trial = Trial(phase)
trial.new()

while True:
    quitEscQ(file)

    bg.fill(Color('white'))

    if trial.isStartScreen:  trial.start()
    else:                    trial.test()

    refresh(screen)
    clock.tick(fps)

# close error log file
sys.stderr.close()
sys.stderr = sys.__stderr__

