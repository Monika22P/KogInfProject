#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate

@atexit.register
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will broke.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='esc'):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error(
            'Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg,
                          height=0.03*SCREEN_RES['height'], wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['esc', 'space'])
    if key == ['esc']:
        abort_with_error(
            'Experiment finished by user on info screen! ESC pressed.')
    win.flip()


def abort_with_error(err):
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)


# GLOBALS
RESULTS = list()   # list in which data will be colected
RESULTS.append(['PART_ID', 'Block_no', 'Trial_no', 'Session_name', 'Reaction_time', 'Key_pressed', 'Stimulus_type', 'Corr_in_trial'])   # Results header


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info = {'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K", "NB"], 'WIEK': '18'}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Test Flankerów, podaj swoje dane:')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock = core.Clock()
    # load config, all params are there
    conf = yaml.safe_load(open('config.yaml', encoding='utf-8'))

    # === Scene init ===
    win = visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix', screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)
    FRAME_RATE = get_frame_rate(win)

    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed for milisecond precision
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText('Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID = info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === Prepared stimulus ===
    fix_cross = visual.TextStim(win, text='+', height=conf['FIX_CROSS_SIZE'], color=conf['FIX_CROSS_COLOR'])
    stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])
    reminder = visual.TextStim(win, text='X lub C   \t\t\t\t   V lub B', height=25, color='dimgray', pos=[0, (SCREEN_RES['height']/2)-50])

    # === Opening message with instruction ===
    show_info(win, join('.', 'messages', 'hello.txt'))

    # === Training ===
    trial_no = 1
    show_info(win, join('.', 'messages', 'before_training.txt'))
    show_info(win, join('.', 'messages', 'reminder.txt'))

    for _ in range(conf['NO_TRAINING_TRIALS']):

        # calling run_trial function and saving data that it returns
        key_pressed, rt, stim_type = run_trial(win, conf, clock, fix_cross, stim, reminder)
        # checking if the answer were correct

        if rt == -1.0:
            corr = "Nie wci?ni?to ?adnego przycisku!"
        elif len(stim_type) > 5:
            if key_pressed == 'a' and (stim_type.find("X", 4, 5) != -1 or stim_type.find("C", 4, 5) != -1):
                corr = "Poprawnie"
            elif key_pressed == 'l' and (stim_type.find("B", 4, 5) != -1 or stim_type.find("V", 4, 5) != -1):
                corr = "Poprawnie"
            else:
                corr = "Niepoprawnie"
        else:
            if key_pressed == 'a' and (stim_type.find("X", 0, 1) != -1 or stim_type.find("C", 0, 1) != -1):
                corr = "Poprawnie"
            elif key_pressed == 'l' and (stim_type.find("B", 0, 1) != -1 or stim_type.find("V", 0, 1) != -1):
                corr = "Poprawnie"
            else:
                corr = "Niepoprawnie"
        # adding user result to the global list with data
        RESULTS.append([PART_ID, '-1', trial_no, 'training', rt, key_pressed, stim_type, corr])

        # presenting user with feedback
        feedb = visual.TextStim(win, text=corr, height=conf['FEEDBACK_SIZE'], color='dimgray')
        feedb.draw()
        reminder.draw()
        win.flip()
        core.wait(2)
        for _ in range(conf['BREAK_TIME']):
            reminder.draw()
            win.flip()
            check_exit()
        trial_no += 1

     # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))
    show_info(win, join('.', 'messages', 'reminder.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['INTRA_BLOCK_TRAINIG']):
            key_pressed, rt, stim_type = run_trial(win, conf, clock, fix_cross, stim, reminder)
            RESULTS.append([PART_ID, block_no, trial_no, 'experiment', rt, key_pressed, stim_type])
            trial_no += 1
            for _ in range(conf['BREAK_TIME']):
                reminder.draw()
                win.flip()
        if block_no != conf['NO_BLOCKS']-1:
            show_info(win, join('.', 'messages', 'break.txt'))

        # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(win, conf, clock, fix_cross, stim, reminder):

    # === Prepared trial-related stimulus ===
    stim.text = random.choice(conf['STIM_TYPES'])

    # === Start pre-trial stuff===
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        reminder.draw()
        win.flip()
        check_exit()

    # === Start trial ===
    event.clearEvents()
    # making sure that clock will be reset exactly when stimuli will be drawn
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):  # present stimuli
        check_exit()
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        if reaction:  # break if any button was pressed
            break
        reminder.draw()
        stim.draw()
        win.flip()

    # === Trial ended, prepare data for send  ===
    if reaction:
        key_pressed, rt = reaction[0]
        stim_type = stim.text
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0
        stim_type = stim.text

    return key_pressed, rt, stim_type  # return all data collected during trial


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
