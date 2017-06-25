#!/usr/bin/env python

#  ______ _ _      _             
# |  ____| (_)    | |            
# | |__  | |_  ___| | _____ _ __ 
# |  __| | | |/ __| |/ / _ \ '__|
# | |    | | | (__|   <  __/ |   
# |_|    |_|_|\___|_|\_\___|_|   
                                
# max. of 5 session blocks per day, i.e. max 5*90 trials

from __future__ import division
import sys
sys.path.append('c:/')
sys.path.append('..')
from lrc import *

# open file for error log
sys.stderr = open('errorlog.txt', 'w')

# HELPER CLASSES
class Image(Box):
    """
    Image class. Loads image #`index` from `stimuli` list/folder. 
    Image is scaled by scaling factor and centered at (400, 150).
    """
    def __init__(self, index):
        super(Image, self).__init__()
        self.image = pygame.image.load(files[index]).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.pos = (400, 175)
        self.mask = pygame.mask.from_surface(self.image)
        self.name = files[index][15:-4]

class Button(Box):
    """Button class for the correct and incorrect icons."""
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
    def __init__(self, phase):
        """Initialise trial with properties set to 0 or empty. `start` is True 
           when search display is presented, False when choice occurs."""
        self.phase = phase
        self.block = 0
        self.number = 0
        self.numCorrect = 0
        self.stimuli = []
        self.isChanged = None
        self.wasCorrect = None
        self.t0 = 0
        self.RT = 0
        self.screen = 'Start'

    def new(self):
        """
        Determine block and trial number. Set `screen` to 'Start' to present 
        start box. Make stimuli and reset cursor.
        """
        if self.number % BLOCK_LENGTH == 0:
            self.newBlock()

        self.number += 1
        self.screen = 'Start'
        self.isChanged = int(random.getrandbits(1))

        if phase == 'Training': self.params = [5000, 0]
        else:                   self.params = paramList[self.number]

        self.makeStimuli()
        cursor.mv2pos((400, 350))

    def repeat(self):
        """
        Repeat trial with different stimuli but same parameters otherwise. 
        Set `screen` to 'Start' to present start box. Make stimuli and 
        reset cursor.
        """
        self.screen = 'Start'

        self.makeStimuli()
        cursor.mv2pos((400, 350))

    def newBlock(self):
        """
        Overwrite `data/num_sessions.txt` with finished session number 
        (for training phase only if 80% criterion met). Quit program if 
        criterion for finished sessions was met. Increment block counter, 
        reset trial and numCorrect counts, and pseudo-randomise params for 
        next block.
        """
        global sessionNum

        # if at least one block of test condition completed, increment `num_sessions.txt`
        # if current completed training block met criterion, increment `num_sessions.txt`
        if (phase == 'Test' and self.block == 1) or \
           (phase == 'Training' and self.numCorrect >= .8*BLOCK_LENGTH):
            with open(lastRun, 'w') as sfl:       sfl.write(today)
            with open(sessionFile, 'w') as sfl:
                if lastDate == today:   sfl.write(phase + '\n' + str(sessionNum))
                else:                   sfl.write(phase + '\n' + str(sessionNum + 1))

        # if current completed training block didn't meet criterion, reset `num_sessions.txt`
        elif (phase == 'Training' and self.numCorrect < .8*BLOCK_LENGTH):
            with open(lastRun, 'w') as sfl:       sfl.write('')
            with open(sessionFile, 'w') as sfl:
                if lastDate == today:   sfl.write(phase + '\n' + str(sessionNum - 1))
                else:                   sfl.write(phase + '\n' + str(sessionNum))

        self.block += 1
        self.number = 0
        self.numCorrect = 0
        random.shuffle(paramList)

    def makeStimuli(self):
        """Pick two non-identical stimuli."""
        idx = random.sample(range(len(files)), self.isChanged + 1)
        self.stimuli = [Image(i) for i in idx]

    def start(self):
        """Draw startbox, show search display upon collision."""
        mvCursor(cursor, only = 'up')

        startbox.draw(bg)
        bg.blit(starttext, startpos)
        cursor.draw(bg)

        # collision check
        if cursor.pxCollide(startbox):
            cursor.mv2pos((400, 450))

            # display search display for specified delay
            self.stimuli[0].draw(bg)
            self.screen = 'Sample'

    def sample(self):
        pygame.time.delay(self.params[0])
        self.screen = 'Flicker'

    def flicker(self):
        pygame.time.delay(self.params[1])
        self.screen = 'Test'
        self.t0 = pygame.time.get_ticks()

    def test(self):
        """Display matches, upon selection: pellet (if correct) or timeout
           (if incorrect)."""
        self.stimuli[self.isChanged].draw(bg)

        mvCursor(cursor, only = 'right, left')
        cursor.draw(bg)

        select = cursor.collide(buttons)

        for b in buttons:   b.draw(bg)

        self.RT = pygame.time.get_ticks() - self.t0

        # timeout after 5s --> repeat trial
        if self.RT >= 5000:
            self.RT = 5000
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

            self.screen = 'Outcome'

    def outcome(self):
        if not self.wasCorrect:
            pygame.time.delay(TIMEOUT)

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

file = 'data/' + makeFileName('flicker')
header = ['monkey', 'date', 'time', 'phase', 'block', 'trial', 'isChanged?', 'search_img', 'test_img', 'dur_search', 'dur_flicker', 'RT', 'wasCorrect?']
writeLn(file, header)
# print header


# set parameters
BLOCK_LENGTH = 90
DURATION_SEARCH_DISPLAY = [250, 500, 1000, 2500, 5000]
DURATION_MASK = [0, 50, 100, 250, 500, 1000]
REPS = 3
TIMEOUT = 3000

# set screen; define cursor; make left/right positions
screen = setScreen()
cursor = Box(circle = True)

# define start box
startbox = Box(col = Color('grey75'), pos = (400, 175), size = (150, 80))
font = pygame.font.SysFont('Arial', 14)
starttext = font.render('Start', 1, Color('black'))
startpos = starttext.get_rect(centerx = 400, centery = 175)

# define buttons
buttons = [Button('change.png', (200, 450)), Button('nochange.png', (600, 450))]

# create list of delays for a block (for pseudo-randomisation)
# delayList = delay * reps
paramList = []

if phase != 'Training':
    for r in range(REPS):
        for d_search in DURATION_SEARCH_DISPLAY:
            for d_mask in DURATION_MASK:
                paramList.append([d_search, d_mask])

# load file list
if phase == 'Training': files = glob.glob('phase1_stimuli/*.gif')
else:                   files = glob.glob('phase2_stimuli/*.GIF')

# start clock
clock = pygame.time.Clock()


# MAIN GAME LOOP: start first trial
trial = Trial(phase)
trial.new()

while True:
    quitEscQ(file)

    bg.fill(Color('white'))

    if trial.screen == 'Start':      trial.start()
    elif trial.screen == 'Sample':   trial.sample()
    elif trial.screen == 'Flicker':  trial.flicker()
    elif trial.screen == 'Test':     trial.test()
    else:                            trial.outcome()

    refresh(screen)
    clock.tick(fps)

# close error log file
sys.stderr.close()
sys.stderr = sys.__stderr__

