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
import sys
sys.path.append('c:/')
sys.path.append('..')
from lrc import *

# open file for error log
sys.stderr = open('errorlog.txt', 'w')

# HELPER CLASSES
def delay(milliseconds):
    """
    Wait for a number of milliseconds. Still allows to quit out of 
    programme.
    """
    elapsed = 0
    while elapsed < milliseconds/1000:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_q):
                pygame.quit()
                sys.exit()
            if event.type == TICK:
                elapsed += 1

class Image(Box):
    """Load image #`index` from `files` list and center it at (400, 150). """
    def __init__(self, index):
        super(Image, self).__init__()
        self.image = pygame.image.load(files[index]).convert_alpha()
        if files[index][-4:]:
            self.image = pygame.transform.smoothscale(self.image, (233, 200))
        self.rect = self.image.get_rect()
        self.rect.center = self.pos = (400, 175)
        self.mask = pygame.mask.from_surface(self.image)
        self.name = files[index][15:-4]

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
        if self.phase == 'Training':    self.block = 0
        else:                           self.block = sessionNum
        self.number = 0
        self.numCorrect = 0
        self.stimuli = []
        self.isChanged = None
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

        self.number += 1
        self.isStartScreen = True
        self.isChanged = isChangedList[self.number - 1]

        if phase == 'Training': self.params = [5000, 0]
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

        if phase == 'Training' and self.block > 0:
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

        if ('Test' in self.phase) and (self.block >= NUM_SESSIONS):
            pygame.quit()
            sys.exit()

        self.block += 1
        self.number = 0
        self.numCorrect = 0
        random.shuffle(isChangedList)
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

        self.stimuli = [Image(self.idx)]

        if self.isChanged:
            lst = range(0, self.idx) + range(self.idx + 1, len(files))
            self.stimuli += [Image(random.choice(lst))]

    def start(self):
        """Draw startbox, show sample upon collision."""
        mvCursor(cursor, only = 'up')

        startbox.draw(bg)
        bg.blit(starttext, startpos)
        cursor.draw(bg)

        if cursor.pxCollide(startbox):
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

        data = [monkey, today, now, phase, self.block, self.number, self.isChanged] + names + self.params + [self.RT, self.wasCorrect]
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
    phase = 'Training'
    sessionNum = 0

if os.path.exists(lastRun):
    with open(lastRun) as lfl:
        lastDate = lfl.read()
else:
    lastDate = ''

if phase == 'Training': critSessionNum = 2
else:                   critSessionNum = 20

if sessionNum >= critSessionNum:
    pygame.quit()
    sys.exit()

# make data file w/ header
if not os.path.exists('data'):
    os.makedirs('data')

file = 'data/' + makeFileName('2change')
header = ['monkey', 'date', 'time', 'phase', 'block', 'trial', 'isChanged?', 'search_img', 'test_img', 'dur_search', 'dur_flicker', 'RT', 'wasCorrect?']
writeLn(file, header)
# print header


# set parameters
if phase == 'Training':
    BLOCK_LENGTH = 90
    REPS = 3
else:
    BLOCK_LENGTH = 120
    REPS = 4

DURATION_SEARCH_DISPLAY = [250, 500, 1000, 2500, 5000]
DURATION_MASK = [0, 50, 100, 250, 500, 1000]
RESPONSE_WINDOW = 5000
TIMEOUT = 20000
NUM_SESSIONS = 40

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
isChangedList = BLOCK_LENGTH//2 * [0, 1]

# create list of delays for a block (for pseudo-randomisation)
paramList = []

if phase != 'Training':
    for r in range(REPS):
        for d_search in DURATION_SEARCH_DISPLAY:
            for d_mask in DURATION_MASK:
                paramList.append([d_search, d_mask])

# load file list
if phase == 'Training': files = glob.glob('phase1_stimuli/*.gif')
elif phase == 'Test1':  files = glob.glob('phase2_stimuli/*.bmp')
elif phase == 'Test2':  pass
elif phase == 'Test3':  pass

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

